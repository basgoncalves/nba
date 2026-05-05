import os
import time
import threading
import urllib.request
import cv2
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
from pathlib import Path
from datetime import datetime
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision


_LANDMARK_NAMES = [
    'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer',
    'right_eye_inner', 'right_eye', 'right_eye_outer',
    'left_ear', 'right_ear', 'mouth_left', 'mouth_right',
    'left_shoulder', 'right_shoulder',
    'left_elbow', 'right_elbow',
    'left_wrist', 'right_wrist',
    'left_pinky', 'right_pinky',
    'left_index', 'right_index',
    'left_thumb', 'right_thumb',
    'left_hip', 'right_hip',
    'left_knee', 'right_knee',
    'left_ankle', 'right_ankle',
    'left_heel', 'right_heel',
    'left_foot_index', 'right_foot_index',
]


# ======================================================================
# Model configuration
# ======================================================================

class MotModelConfig:
    """Defines the column layout for an OpenSim MOT file.

    Parameters
    ----------
    name : str
        Short identifier used in log messages and the MOT header.
    osim_path : str
        Absolute path to the .osim model file (informational only; not loaded).
    angle_columns : list of 7-tuples
        Each tuple: (col_name, lm_a, lm_vertex, lm_b, offset, clip_min, clip_max)

        * col_name   – column label written to the header row.
        * lm_a/b     – MediaPipe landmark names for the two outer points.
        * lm_vertex  – MediaPipe landmark name for the joint centre.
        * offset     – value subtracted from the raw angle before writing
                       (use 180 for the OpenSim elevation/flex complement
                       convention, 0 for the raw angle).
        * clip_min/max – output is clipped to [clip_min, clip_max].
    include_ball : bool
        If True, append six ball columns after the angle columns:
        ball_rx, ball_ry, ball_rz, ball_tx, ball_ty, ball_tz.
    ball_anchor_landmark : str
        Pose landmark used as the local origin for ball translation.
        Defaults to 'right_shoulder'.
    """

    def __init__(self, name, osim_path, angle_columns, include_ball=False,
                 ball_anchor_landmark='right_shoulder'):
        self.name = name
        self.osim_path = osim_path
        self.angle_columns = angle_columns
        self.include_ball = include_ball
        self.ball_anchor_landmark = ball_anchor_landmark

    @property
    def column_names(self):
        names = ['time'] + [c[0] for c in self.angle_columns]
        if self.include_ball:
            names += ['ball_rx', 'ball_ry', 'ball_rz', 'ball_tx', 'ball_ty', 'ball_tz']
        return names

    @property
    def n_columns(self):
        return len(self.column_names)


# ------------------------------------------------------------------
# Predefined model configs
# ------------------------------------------------------------------

# arm26_ball.osim — right arm only, includes ball object
# Coordinates: r_shoulder_elev, r_elbow_flex + 6 ball DOFs
ARM26_BALL_CONFIG = MotModelConfig(
    name='arm26_ball',
    osim_path=r'C:\OpenSim 4.4\Resources\Models\Arm26\arm26_ball.osim',
    angle_columns=[
        # (col_name, lm_a, lm_vertex, lm_b, offset, clip_min, clip_max)
        ('r_shoulder_elev', 'right_hip',      'right_shoulder', 'right_elbow', 180, 0, 180),
        ('r_elbow_flex',    'right_shoulder', 'right_elbow',    'right_wrist', 180, 0, 130),
    ],
    include_ball=True,
    ball_anchor_landmark='right_shoulder',
)

# Bilateral Upper Extremity Trunk Model — both arms, no ball object
# NOTE: Verify the coordinate names below match those in the .osim file.
#       Open the model in OpenSim > Coordinates panel to confirm, then
#       update col_name strings if needed.
BUET_CONFIG = MotModelConfig(
    name='buet',
    osim_path=(r'C:\OpenSim 4.4\Resources\Models\BUET Model'
               r'\Bilateral Upper Extremity Trunk Model_with_ball.osim'),
    angle_columns=[
        # Right arm — coordinate names from OpenSim Coordinates panel
        ('arm_flex_r',   'right_hip',      'right_shoulder', 'right_elbow', 180, -90, 180),
        ('elbow_flex_r', 'right_shoulder', 'right_elbow',    'right_wrist', 180,   0, 150),
        # Left arm
        ('arm_flex_l',   'left_hip',       'left_shoulder',  'left_elbow',  180, -90, 180),
        ('elbow_flex_l', 'left_shoulder',  'left_elbow',     'left_wrist',  180,   0, 150),
    ],
    include_ball=True,
)

# Full-body config — both arms (incl. wrist) + both legs (hip + knee)
# Not tied to a specific .osim; useful for the joint_angles plot and
# general-purpose MOT export when a full-body model is used.
FULL_BODY_CONFIG = MotModelConfig(
    name='full_body',
    osim_path='',
    angle_columns=[
        # Right arm
        ('r_shoulder_flex', 'right_hip',      'right_shoulder', 'right_elbow',  180, -90, 180),
        ('r_elbow_flex',    'right_shoulder', 'right_elbow',    'right_wrist',  180,   0, 150),
        ('r_wrist_ext',     'right_elbow',    'right_wrist',    'right_index',  180, -90,  90),
        # Left arm
        ('l_shoulder_flex', 'left_hip',       'left_shoulder',  'left_elbow',   180, -90, 180),
        ('l_elbow_flex',    'left_shoulder',  'left_elbow',     'left_wrist',   180,   0, 150),
        ('l_wrist_ext',     'left_elbow',     'left_wrist',     'left_index',   180, -90,  90),
        # Right leg
        ('r_hip_flex',      'right_shoulder', 'right_hip',      'right_knee',   180, -30, 120),
        ('r_knee_flex',     'right_hip',      'right_knee',     'right_ankle',  180,   0, 150),
        # Left leg
        ('l_hip_flex',      'left_shoulder',  'left_hip',       'left_knee',    180, -30, 120),
        ('l_knee_flex',     'left_hip',       'left_knee',      'left_ankle',   180,   0, 150),
    ],
    include_ball=True,
)


class MovementTracker:
    """Track human movement and ball trajectory from a camera feed.

    One record is stored per video frame:
        (annotated_bgr_frame, wall_clock_time, pose_lm_dict_or_None, ball_center_or_None)

    Outputs
    -------
    save_frames()         — every frame annotated with skeleton + ball path → folder
    plot_joint_angles()   — shoulder & elbow angle time-series → PNG
    analyze_release()     — two-panel release (top) / catch (bottom) figure → PNG
    write_opensim_mot()   — full-session MOT for arm26_ball.osim → .mot
    """

    def __init__(self, max_trajectory_length=200, hsv_lower=None, hsv_upper=None):
        self.max_trajectory_length = max_trajectory_length
        self.trajectory = deque(maxlen=max_trajectory_length)
        self._records = []          # populated by track_and_display
        self._duration_seconds = 0
        self._frame_shape = None    # (h, w) set on first captured frame

        # MediaPipe Pose (Tasks API)
        model_path = Path("pose_landmarker_lite.task")
        if not model_path.exists():
            url = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
                   "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task")
            print("Downloading pose landmarker model...")
            urllib.request.urlretrieve(url, model_path)
            print("Model downloaded.")
        base_opts = mp_python.BaseOptions(model_asset_path=str(model_path))
        self._pose_landmarker = mp_vision.PoseLandmarker.create_from_options(
            mp_vision.PoseLandmarkerOptions(base_options=base_opts, num_poses=1)
        )

        # Ball HSV colour range (default: green ball)
        self.hsv_lower = hsv_lower if hsv_lower is not None else np.array([35, 50, 30])
        self.hsv_upper = hsv_upper if hsv_upper is not None else np.array([85, 255, 255])

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _test_camera(self, camera_type='webcam'):
        """Test if the specified camera can be opened."""
        cap = cv2.VideoCapture(0 if camera_type == 'webcam' else "http://192.168.0.107:8080/video")
        if not cap.isOpened():
            print(f"Error: Unable to open {camera_type} camera.")
        cap.release()

    def record_video(self, duration_seconds=10, camera_type='webcam', output_dir=None,
                     target_fps=None, detection_interval=1):
        """Record raw camera footage for `duration_seconds` and save as video.mp4.

        Frames are also stored in self._records so all analysis methods
        (save_frames, plot_joint_angles, etc.) work normally afterward.

        Parameters
        ----------
        duration_seconds : int or float
            How long to record.
        camera_type : str
            'webcam' for device 0, 'ip' for IP Webcam stream.
        output_dir : str or Path, optional
            Folder to write video.mp4 into.  Created if it does not exist.
            Defaults to outputs/test_<timestamp>/.
        target_fps : float, optional
            Override the camera-reported FPS for the VideoWriter.
            Useful when the camera reports an incorrect value or you want
            to record at a specific rate (e.g. 60).  Defaults to the value
            reported by cv2.CAP_PROP_FPS (fallback 30).
        detection_interval : int
            Run pose + ball detection only every N frames.  Set to 1 (default)
            for every frame; increase (e.g. 2 or 3) to raise the effective
            capture frame rate when processing is the bottleneck.  Frames
            that skip detection reuse the last known landmark / ball result.

        Returns
        -------
        Path
            Path to the saved .mp4 file.
        """
        if output_dir is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path(f"outputs/test_{ts}")
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        self._duration_seconds = duration_seconds
        self._records.clear()
        self.trajectory.clear()

        src = 0 if camera_type == 'webcam' else "http://192.168.0.107:8080/video"
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            print(f"Error: Cannot open {camera_type} camera.")
            return None

        cam_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        fps = float(target_fps) if target_fps else cam_fps
        w    = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h    = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # IP camera streams in portrait orientation rotated 90° CCW — swap dims
        if camera_type != 'webcam':
            w, h = h, w
        if self._frame_shape is None:
            self._frame_shape = (h, w)

        video_path = output_dir / "video.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(str(video_path), fourcc, fps, (w, h))

        detection_interval = max(1, int(detection_interval))

        # --- Background reader thread: drains camera buffer at full speed ---
        _stop = threading.Event()
        _latest = [None]   # holds (timestamp, frame) — always the newest

        def _reader():
            while not _stop.is_set():
                ret, f = cap.read()
                if not ret:
                    _stop.set(); break
                if camera_type != 'webcam':
                    f = cv2.rotate(f, cv2.ROTATE_90_COUNTERCLOCKWISE)
                _latest[0] = (time.time(), f)

        reader_thread = threading.Thread(target=_reader, daemon=True)
        reader_thread.start()
        while _latest[0] is None and not _stop.is_set():
            time.sleep(0.001)

        print(f"Recording {duration_seconds}s @ {fps:.0f} fps "
              f"(detect every {detection_interval} frame(s)) → {video_path.resolve()} …")
        session_start = time.time()
        frame_idx = 0
        last_pose_lm, last_center = None, None
        last_t = 0.0

        while (time.time() - session_start) < duration_seconds and not _stop.is_set():
            item = _latest[0]
            if item is None:
                time.sleep(0.001); continue
            t, frame = item
            if t == last_t:          # no new frame yet
                time.sleep(0.0005); continue
            last_t = t

            writer.write(frame)

            # Pose + ball — only every detection_interval frames
            if frame_idx % detection_interval == 0:
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB,
                                  data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                pose_result = self._pose_landmarker.detect(mp_img)
                last_pose_lm = None
                if pose_result.pose_landmarks:
                    last_pose_lm = {
                        name: (lm.x * w, lm.y * h)
                        for name, lm in zip(_LANDMARK_NAMES, pose_result.pose_landmarks[0])
                    }
                last_center = self._detect_ball(frame)

            if last_center:
                self.trajectory.append(last_center)

            self._records.append((frame.copy(), t, last_pose_lm, last_center))
            frame_idx += 1
            cv2.imshow('Recording', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        _stop.set()
        reader_thread.join(timeout=2)
        writer.release()
        cap.release()
        cv2.destroyAllWindows()

        elapsed = time.time() - session_start
        ball_count = sum(1 for r in self._records if r[3] is not None)
        actual_fps = len(self._records) / elapsed if elapsed > 0 else 0
        print(f"Saved {len(self._records)} frames ({elapsed:.1f}s, {actual_fps:.1f} fps actual) — "
              f"{ball_count} with ball detected.")
        print(f"Video : {video_path.resolve()}")
        return video_path

    def _detect_ball(self, frame):
        """Return (cx, cy) of best circular green blob, or None."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        best, best_score = None, 0
        for c in contours:
            area = cv2.contourArea(c)
            if area < 1500:
                continue
            p = cv2.arcLength(c, True)
            if p == 0:
                continue
            circ = (4 * np.pi * area) / (p ** 2)
            if circ < 0.55:
                continue
            score = area * circ
            if score > best_score:
                best_score, best = score, c
        if best is not None:
            M = cv2.moments(best)
            if M["m00"] != 0:
                return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        return None

    @staticmethod
    def _angle_between(a, vertex, b):
        """Angle in degrees at `vertex` formed by points a-vertex-b."""
        va = np.array(a) - np.array(vertex)
        vb = np.array(b) - np.array(vertex)
        cos_a = np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-9)
        return float(np.degrees(np.arccos(np.clip(cos_a, -1.0, 1.0))))

    def _wrist_pts(self, lm):
        """Return list of (x, y) wrist positions from a pose landmark dict."""
        if lm is None:
            return []
        pts = []
        for k in ('left_wrist', 'right_wrist'):
            p = lm.get(k)
            if p is not None:
                pts.append(p)
        return pts

    def _ball_records(self):
        """Frames with ball detected: list of (record_index, timestamp, ball_center)."""
        return [(i, r[1], r[3]) for i, r in enumerate(self._records) if r[3] is not None]

    # ------------------------------------------------------------------
    # Capture
    # ------------------------------------------------------------------

    def track_and_display(self, duration_seconds=10, camera_type='webcam',
                          detection_interval=1):
        """Run the camera loop for `duration_seconds` wall-clock seconds.

        Every frame is stored in self._records with full annotations
        already drawn (pose skeleton + trajectory) in BGR.

        Parameters
        ----------
        detection_interval : int
            Run pose + ball detection only every N frames (default 1 = every
            frame).  Increase to raise effective capture rate when inference
            is the bottleneck; skipped frames reuse the last known result.
        """
        self._duration_seconds = duration_seconds
        self._records.clear()
        self.trajectory.clear()

        cap = cv2.VideoCapture(
            0 if camera_type == 'webcam' else "http://192.168.0.107:8080/video"
        )
        if not cap.isOpened():
            print("Error: Cannot open camera.")
            return

        detection_interval = max(1, int(detection_interval))

        # --- Background reader thread ---
        _stop = threading.Event()
        _latest = [None]

        def _reader():
            while not _stop.is_set():
                ret, f = cap.read()
                if not ret:
                    _stop.set(); break
                if camera_type != 'webcam':
                    f = cv2.rotate(f, cv2.ROTATE_90_CLOCKWISE)
                _latest[0] = (time.time(), f)

        reader_thread = threading.Thread(target=_reader, daemon=True)
        reader_thread.start()
        while _latest[0] is None and not _stop.is_set():
            time.sleep(0.001)
        if self._frame_shape is None and _latest[0]:
            self._frame_shape = _latest[0][1].shape[:2]

        print(f"Tracking for {duration_seconds} seconds "
              f"(detect every {detection_interval} frame(s)). Press 'q' to stop.")
        session_start = time.time()
        frame_idx = 0
        last_pose_lm, last_center = None, None
        last_t = 0.0

        while (time.time() - session_start) < duration_seconds and not _stop.is_set():
            item = _latest[0]
            if item is None:
                time.sleep(0.001); continue
            t, frame = item
            if t == last_t:
                time.sleep(0.0005); continue
            last_t = t
            frame = frame.copy()

            # --- Pose estimation (every detection_interval frames) ---
            if frame_idx % detection_interval == 0:
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB,
                                  data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                pose_result = self._pose_landmarker.detect(mp_img)
                last_pose_lm = None
                if pose_result.pose_landmarks:
                    h_f, w_f = frame.shape[:2]
                    last_pose_lm = {
                        name: (lm.x * w_f, lm.y * h_f)
                        for name, lm in zip(_LANDMARK_NAMES, pose_result.pose_landmarks[0])
                    }
                last_center = self._detect_ball(frame)

            pose_lm = last_pose_lm
            center  = last_center

            # --- Draw full skeleton (arms + legs) ---
            if pose_lm is not None:
                all_joints = ('left_shoulder', 'right_shoulder',
                              'left_elbow', 'right_elbow',
                              'left_wrist', 'right_wrist',
                              'left_hip', 'right_hip',
                              'left_knee', 'right_knee',
                              'left_ankle', 'right_ankle')
                for joint in all_joints:
                    if joint in pose_lm:
                        jx, jy = int(pose_lm[joint][0]), int(pose_lm[joint][1])
                        cv2.circle(frame, (jx, jy), 5, (255, 100, 0), -1)
                for side in ('left', 'right'):
                    arm = [pose_lm.get(f'{side}_{j}')
                           for j in ('shoulder', 'elbow', 'wrist')]
                    leg = [pose_lm.get(f'{side}_{j}')
                           for j in ('hip', 'knee', 'ankle')]
                    for chain, color in ((arm, (255, 100, 0)), (leg, (0, 200, 100))):
                        for a, b in zip(chain, chain[1:]):
                            if a and b:
                                cv2.line(frame, (int(a[0]), int(a[1])),
                                         (int(b[0]), int(b[1])), color, 2)
                    # trunk line (shoulder → hip)
                    sh = pose_lm.get(f'{side}_shoulder')
                    hp = pose_lm.get(f'{side}_hip')
                    if sh and hp:
                        cv2.line(frame, (int(sh[0]), int(sh[1])),
                                 (int(hp[0]), int(hp[1])), (180, 60, 220), 2)

            # --- Ball ---
            if center:
                self.trajectory.append(center)
                cv2.circle(frame, center, 10, (0, 255, 0), 2)

            # --- Trajectory overlay ---
            if len(self.trajectory) > 1:
                pts = np.array(list(self.trajectory), dtype=np.int32)
                cv2.polylines(frame, [pts], False, (0, 255, 255), 2)

            self._records.append((frame.copy(), t, pose_lm, center))
            frame_idx += 1
            cv2.imshow('Movement Tracker', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        _stop.set()
        reader_thread.join(timeout=2)
        cap.release()
        cv2.destroyAllWindows()
        ball_count = sum(1 for r in self._records if r[3] is not None)
        elapsed = time.time() - session_start
        actual_fps = len(self._records) / elapsed if elapsed > 0 else 0
        print(f"Captured {len(self._records)} frames ({actual_fps:.1f} fps actual), "
              f"{ball_count} with ball detected.")

    # ------------------------------------------------------------------
    # Save ALL annotated frames
    # ------------------------------------------------------------------

    def save_frames(self, folder):
        """Save every captured frame as a PNG.

        Each image shows the pose skeleton with joint-angle labels (shoulder
        and elbow), the full ball trajectory, and the ball position for that
        frame highlighted.  Frames are written to `folder/frame_NNNNN.png`.
        """
        if not self._records:
            print("No frames to save.")
            return
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)

        ball_pts_list = [r[3] for r in self._records if r[3] is not None]
        all_ball = np.array(ball_pts_list) if len(ball_pts_list) >= 2 else None

        _txt_kw = dict(fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.60))

        total = len(self._records)
        print(f"Saving {total} annotated frames to {folder.resolve()} …")
        for fi, (frame_bgr, t, lm, center) in enumerate(self._records):
            fig, ax = plt.subplots(figsize=(10, 7))
            ax.imshow(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))

            # Ball trajectory path
            if all_ball is not None:
                ax.plot(all_ball[:, 0], all_ball[:, 1], 'c-', linewidth=1.5, alpha=0.7)
                ax.plot(all_ball[0, 0],  all_ball[0, 1],  'go', markersize=5)
                ax.plot(all_ball[-1, 0], all_ball[-1, 1], 'ro', markersize=5)

            # Ball dot this frame
            if center is not None:
                ax.plot(center[0], center[1], 'o', color='lime', markersize=9,
                        markeredgecolor='white', markeredgewidth=1.5, zorder=6)

            # Pose skeleton + angle labels
            if lm is not None:
                for side, color in (('left', '#e07b39'), ('right', '#39a7e0')):
                    hip      = lm.get(f'{side}_hip')
                    shoulder = lm.get(f'{side}_shoulder')
                    elbow    = lm.get(f'{side}_elbow')
                    wrist    = lm.get(f'{side}_wrist')
                    for a, b in ((hip, shoulder), (shoulder, elbow), (elbow, wrist)):
                        if a and b:
                            ax.plot([a[0], b[0]], [a[1], b[1]], '-',
                                    color=color, lw=1.8, alpha=0.9)
                    for pt in (shoulder, elbow, wrist):
                        if pt:
                            ax.plot(pt[0], pt[1], 'o', color=color, markersize=5,
                                    markeredgecolor='white', markeredgewidth=1, zorder=5)
                    if hip and shoulder and elbow:
                        ang = self._angle_between(hip, shoulder, elbow)
                        ax.text(shoulder[0] + 5, shoulder[1] - 5,
                                f"{ang:.0f}\u00b0", color=color, **_txt_kw)
                    if shoulder and elbow and wrist:
                        ang = self._angle_between(shoulder, elbow, wrist)
                        ax.text(elbow[0] + 5, elbow[1] - 5,
                                f"{ang:.0f}\u00b0", color=color, **_txt_kw)

            ax.set_title(f"Frame {fi + 1} / {total}", fontsize=10)
            ax.axis('off')
            plt.tight_layout()
            fig.savefig(str(folder / f"frame_{fi + 1:05d}.png"), dpi=100, bbox_inches='tight')
            plt.close(fig)

        print(f"Done — {total} frames saved.")

    # ------------------------------------------------------------------
    # Joint angle plot
    # ------------------------------------------------------------------

    def plot_joint_angles(self, save_path=None):
        """Time-series of all detected joint angles — arms and legs, left and right."""
        if not self._records:
            print("No data recorded.")
            return

        # (panel_label, side, [(series_label, lm_a, lm_vertex, lm_b, color)])
        PANELS = [
            ('Left Arm', 'left', [
                ('Shoulder flex', 'left_hip',      'left_shoulder', 'left_elbow',  '#e07b39'),
                ('Elbow flex',    'left_shoulder', 'left_elbow',    'left_wrist',  '#39a7e0'),
                ('Wrist ext',     'left_elbow',    'left_wrist',    'left_index',  '#7ccc60'),
            ]),
            ('Right Arm', 'right', [
                ('Shoulder flex', 'right_hip',      'right_shoulder', 'right_elbow',  '#d94f1e'),
                ('Elbow flex',    'right_shoulder', 'right_elbow',    'right_wrist',  '#1e7fd9'),
                ('Wrist ext',     'right_elbow',    'right_wrist',    'right_index',  '#3daa20'),
            ]),
            ('Left Leg', 'left', [
                ('Hip flex',  'left_shoulder', 'left_hip',   'left_knee',   '#b07ac4'),
                ('Knee flex', 'left_hip',      'left_knee',  'left_ankle',  '#c4a07a'),
            ]),
            ('Right Leg', 'right', [
                ('Hip flex',  'right_shoulder', 'right_hip',   'right_knee',   '#8a4ab0'),
                ('Knee flex', 'right_hip',      'right_knee',  'right_ankle',  '#b08a4a'),
            ]),
        ]

        t0 = self._records[0][1]

        # Collect angles
        panel_data = []   # [(panel_label, [(series_label, color, ts, vals)], ...]
        any_data = False
        for panel_label, side, series_defs in PANELS:
            series_out = []
            for s_label, lm_a, lm_v, lm_b, color in series_defs:
                ts, vals = [], []
                for _, t, lm, _ in self._records:
                    if lm is None:
                        continue
                    pa = lm.get(lm_a)
                    pv = lm.get(lm_v)
                    pb = lm.get(lm_b)
                    if pa and pv and pb:
                        ts.append(t - t0)
                        vals.append(self._angle_between(pa, pv, pb))
                if ts:
                    series_out.append((s_label, color, ts, vals))
                    any_data = True
            panel_data.append((panel_label, series_out))

        if not any_data:
            print("No pose landmarks found in any frame.")
            return

        # Only draw panels that have at least one series with data
        active_panels = [(lbl, s) for lbl, s in panel_data if s]
        n = len(active_panels)
        fig, axes = plt.subplots(n, 1, figsize=(13, 3.5 * n), sharex=True)
        if n == 1:
            axes = [axes]

        for ax, (panel_label, series_list) in zip(axes, active_panels):
            for s_label, color, ts, vals in series_list:
                ax.plot(ts, vals, label=s_label, color=color,
                        linewidth=1.8, marker='o', markersize=2)
            ax.set_ylabel('Angle (\u00b0)', fontsize=10)
            ax.set_title(panel_label, fontsize=11)
            ax.legend(fontsize=9)
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 200)

        axes[-1].set_xlabel('Time (s)', fontsize=10)
        plt.suptitle('Joint Angles Over Time', fontsize=13, fontweight='bold')
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Joint angles saved to {os.path.abspath(save_path)}")
        plt.close()

    # ------------------------------------------------------------------
    # Release / catch two-panel figure
    # ------------------------------------------------------------------

    def analyze_release(self, proximity_threshold=100, velocity_smoothing=5, save_path=None):
        """Detect ball release and catch; save two-panel figure if save_path given.

        Returns dict with release_point, catch_point, vx, vy, speed, angle_deg.
        """
        ball_recs = self._ball_records()
        if len(ball_recs) < velocity_smoothing + 1:
            print("Not enough ball detections for release analysis.")
            return None

        positions   = [c for _, _, c in ball_recs]
        timestamps  = [t for _, t, _ in ball_recs]
        rec_indices = [i for i, _, _ in ball_recs]
        n = len(positions)

        def _min_dist(ball_pos, pts):
            if not pts:
                return float('inf')
            return min(np.hypot(ball_pos[0] - px, ball_pos[1] - py) for px, py in pts)

        # Release: first frame where ball moves from near-wrist to far
        was_close = False
        release_idx = 0
        for i in range(n):
            lm = self._records[rec_indices[i]][2]
            d  = _min_dist(positions[i], self._wrist_pts(lm))
            if d <= proximity_threshold:
                was_close = True
            elif was_close:
                release_idx = i
                break

        # Catch: ball returns near wrist after release
        catch_idx = n - 1
        for i in range(release_idx + 1, n):
            lm = self._records[rec_indices[i]][2]
            if _min_dist(positions[i], self._wrist_pts(lm)) <= proximity_threshold:
                catch_idx = i
                break

        # Velocity at release
        end_idx = min(release_idx + velocity_smoothing, n - 1)
        dt = timestamps[end_idx] - timestamps[release_idx]
        if dt == 0:
            print("Zero elapsed time; cannot compute velocity.")
            return None
        dx = positions[end_idx][0] - positions[release_idx][0]
        dy = positions[end_idx][1] - positions[release_idx][1]
        vx    = dx / dt
        vy    = -dy / dt          # flip: pixel-Y is down
        speed = np.hypot(vx, vy)
        angle_deg     = np.degrees(np.arctan2(vy, vx))
        release_point = positions[release_idx]
        catch_point   = positions[catch_idx]
        flight_time   = timestamps[catch_idx] - timestamps[release_idx]
        flight_dets   = catch_idx - release_idx

        print("\n--- Release & Catch ---")
        print(f"Release : {release_point}  [detection {release_idx}]")
        print(f"Catch   : {catch_point}  [detection {catch_idx}]")
        print(f"Speed   : {speed:.1f} px/s   Angle: {angle_deg:.1f}\u00b0   "
              f"Flight: {flight_time:.3f}s  ({flight_dets} detections)")

        result = {
            'release_point': release_point, 'catch_point': catch_point,
            'vx': vx, 'vy': vy, 'speed': speed, 'angle_deg': angle_deg,
        }
        if save_path is None:
            return result

        rel_frame_bgr = self._records[rec_indices[release_idx]][0]
        cat_frame_bgr = self._records[rec_indices[catch_idx]][0]
        all_pos   = np.array(positions)
        flight_pos = all_pos[release_idx:catch_idx + 1]

        fig, (ax_r, ax_c) = plt.subplots(2, 1, figsize=(13, 14))

        # --- TOP: release panel ---
        ax_r.imshow(cv2.cvtColor(rel_frame_bgr, cv2.COLOR_BGR2RGB))
        ax_r.plot(all_pos[:, 0], all_pos[:, 1], 'c-o',
                  linewidth=2, markersize=3, label='Trajectory', alpha=0.6)
        if len(flight_pos) > 1:
            ax_r.plot(flight_pos[:, 0], flight_pos[:, 1], 'w-',
                      linewidth=2.5, alpha=0.9, label='Flight arc')
        ax_r.plot(*release_point, 'yo', markersize=14,
                  markeredgecolor='white', markeredgewidth=2, label='Release', zorder=5)
        ax_r.text(release_point[0] + 12, release_point[1] - 12, 'Release',
                  color='yellow', fontsize=10, fontweight='bold',
                  bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.55))
        arrow_scale = min(rel_frame_bgr.shape[:2]) * 0.0001
        ax_r.annotate('',
                      xy=(release_point[0] + vx * arrow_scale,
                          release_point[1] - vy * arrow_scale),
                      xytext=release_point,
                      arrowprops=dict(arrowstyle='->', color='yellow', lw=2.5))
        arc_r = min(rel_frame_bgr.shape[:2]) * 0.06
        theta = np.linspace(0, np.radians(angle_deg), 40)
        ax_r.plot(release_point[0] + arc_r * np.cos(theta),
                  release_point[1] - arc_r * np.sin(theta), color='orange', lw=1.5)
        ax_r.text(release_point[0] + arc_r * 1.2 * np.cos(np.radians(angle_deg / 2)),
                  release_point[1] - arc_r * 1.2 * np.sin(np.radians(angle_deg / 2)),
                  f"{angle_deg:.1f}\u00b0", color='orange', fontsize=10, fontweight='bold')
        ax_r.set_title(
            f"RELEASE\n"
            f"Vx={vx:+.0f}  Vy={vy:+.0f}  Speed={speed:.0f} px/s  Angle={angle_deg:.1f}\u00b0",
            fontsize=11)
        ax_r.legend(loc='upper right', fontsize=9)
        ax_r.axis('off')

        # --- BOTTOM: catch panel ---
        ax_c.imshow(cv2.cvtColor(cat_frame_bgr, cv2.COLOR_BGR2RGB))
        ax_c.plot(all_pos[:, 0], all_pos[:, 1], 'c-o',
                  linewidth=2, markersize=3, label='Trajectory', alpha=0.6)
        if len(flight_pos) > 1:
            ax_c.plot(flight_pos[:, 0], flight_pos[:, 1], 'w-',
                      linewidth=2.5, alpha=0.9, label='Flight arc')
        ax_c.plot(*catch_point, 's', color='magenta', markersize=14,
                  markeredgecolor='white', markeredgewidth=2, label='Catch', zorder=5)
        ax_c.text(catch_point[0] + 12, catch_point[1] - 12, 'Catch',
                  color='magenta', fontsize=10, fontweight='bold',
                  bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.55))
        ax_c.set_title(
            f"CATCH\nFlight: {flight_time:.3f}s  ({flight_dets} detections)", fontsize=11)
        ax_c.legend(loc='upper right', fontsize=9)
        ax_c.axis('off')

        plt.suptitle('Release & Catch Analysis', fontsize=13, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Release/catch figure saved to {os.path.abspath(save_path)}")
        plt.close()
        return result

    # ------------------------------------------------------------------
    # OpenSim MOT export
    # ------------------------------------------------------------------

    def write_opensim_mot(self, save_path, model_config=None):
        """Write a full-session MOT file for the given OpenSim model.

        Parameters
        ----------
        save_path : str or Path
            Output path for the .mot file.
        model_config : MotModelConfig, optional
            Column layout and model metadata.  Defaults to ARM26_BALL_CONFIG
            (right arm + ball, matching arm26_ball.osim).  Pass BUET_CONFIG
            (or any custom MotModelConfig) for a different model.
        """
        if model_config is None:
            model_config = ARM26_BALL_CONFIG
        if not self._records:
            print("No data to write.")
            return

        # Pixel-to-metre scale — use both arm sides for robustness
        scale_samples = []
        for _, _, lm, _ in self._records:
            if lm is None:
                continue
            for side in ('right', 'left'):
                sh = lm.get(f'{side}_shoulder')
                el = lm.get(f'{side}_elbow')
                wr = lm.get(f'{side}_wrist')
                if sh and el and wr:
                    arm_px = (np.hypot(el[0] - sh[0], el[1] - sh[1]) +
                              np.hypot(wr[0] - el[0], wr[1] - el[1]))
                    if arm_px > 10:
                        scale_samples.append(0.55 / arm_px)
        px_to_m = (float(np.median(scale_samples)) if scale_samples
                   else 1.8 / (self._frame_shape[0] if self._frame_shape else 720))

        # Ball lookup table (detected frames only)
        ball_ts   = np.array([r[1] for r in self._records if r[3] is not None], dtype=float)
        ball_px_x = np.array([r[3][0] for r in self._records if r[3] is not None], dtype=float)
        ball_px_y = np.array([r[3][1] for r in self._records if r[3] is not None], dtype=float)
        has_ball  = model_config.include_ball and len(ball_ts) > 0

        t0 = self._records[0][1]
        rows = []
        for _, t, lm, _ in self._records:
            rel_t = t - t0

            # --- Angle columns defined by the config ---
            angle_vals = []
            for col_name, lm_a, lm_vertex, lm_b, offset, clip_min, clip_max \
                    in model_config.angle_columns:
                if lm is not None:
                    pa = lm.get(lm_a)
                    pv = lm.get(lm_vertex)
                    pb = lm.get(lm_b)
                    if pa and pv and pb:
                        val = float(np.clip(
                            offset - self._angle_between(pa, pv, pb),
                            clip_min, clip_max))
                    else:
                        val = 0.0
                else:
                    val = 0.0
                angle_vals.append(val)

            # --- Ball columns (optional) ---
            if has_ball:
                anchor = (lm.get(model_config.ball_anchor_landmark)
                          if lm is not None else None)
                tc  = float(np.clip(t, ball_ts[0], ball_ts[-1]))
                bpx = float(np.interp(tc, ball_ts, ball_px_x))
                bpy = float(np.interp(tc, ball_ts, ball_px_y))
                if anchor is not None:
                    btx = (bpx - anchor[0]) * px_to_m
                    bty = -(bpy - anchor[1]) * px_to_m   # flip: pixel-Y down
                else:
                    btx, bty = bpx * px_to_m, -bpy * px_to_m
                ball_vals = [0.0, 0.0, 0.0, btx, bty, 0.3]
            elif model_config.include_ball:
                # ball requested but no detections
                ball_vals = [0.0, 0.0, 0.0, 0.0, 0.0, 0.3]
            else:
                ball_vals = []

            rows.append([rel_t] + angle_vals + ball_vals)

        # Pad to exactly reach requested duration
        if rows and rows[-1][0] < self._duration_seconds - 0.001:
            rows.append([self._duration_seconds] + rows[-1][1:])

        col_header = '\t'.join(model_config.column_names)
        save_path = Path(save_path)
        with open(save_path, 'w') as f:
            f.write(f"{model_config.name}_from_video\n")
            f.write("version=1\n")
            f.write(f"nRows={len(rows)}\n")
            f.write(f"nColumns={model_config.n_columns}\n")
            f.write("inDegrees=yes\n\n")
            f.write("endheader\n")
            f.write(col_header + '\n')
            for row in rows:
                f.write('\t'.join(
                    f"{v:.6f}" if i == 0 else f"{v:.4f}"
                    for i, v in enumerate(row)
                ) + '\n')

        print(f"MOT saved to {os.path.abspath(save_path)}")
        print(f"  Model   : {model_config.name}")
        print(f"  .osim   : {model_config.osim_path}")
        print(f"  Rows    : {len(rows)}  (~{rows[-1][0]:.2f} s)")
        print(f"  px\u2192m    : {px_to_m:.5f}  "
              f"({'arm joints' if scale_samples else 'frame-height fallback'})")
        print(f"  Columns : {', '.join(model_config.column_names)}")


def main():
    # --- Quick recording session ---
    DURATION   = 10     # seconds to record
    CAMERA     = 'ip'   # 'webcam' or 'ip'
    # target_fps sets the VideoWriter playback rate; actual captured fps depends
    # on the camera.  Set to None to use the camera-reported value.
    FPS        = None   # e.g. 30, 60, or None
    # Run pose+ball detection every N frames.  Increase to reduce CPU load;
    # skipped frames reuse the last known result.
    DETECT_INT = 2

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(f"outputs/test_{timestamp}")

    tracker = MovementTracker()
    tracker.record_video(duration_seconds=DURATION, camera_type=CAMERA,
                         output_dir=out, target_fps=FPS, detection_interval=DETECT_INT)

    # Analysis pipeline
    tracker.save_frames(out / "frames")
    tracker.plot_joint_angles(save_path=str(out / "joint_angles.png"))
    tracker.analyze_release(save_path=str(out / "release_catch.png"))
    tracker.write_opensim_mot(save_path=str(out / "arm26_ball_motion.mot"),
                              model_config=ARM26_BALL_CONFIG)
    tracker.write_opensim_mot(save_path=str(out / "buet_motion.mot"),
                              model_config=BUET_CONFIG)
    tracker.write_opensim_mot(save_path=str(out / "full_body_motion.mot"),
                              model_config=FULL_BODY_CONFIG)


if __name__ == "__main__":
    main()
