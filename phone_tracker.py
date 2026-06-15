"""
phone_tracker.py
────────────────
Reads the Android accelerometer via the SensorServer app (WebSocket).

How tilt → steering:
  The phone is held horizontally like a steering wheel.
  Accelerometer X-axis = left/right tilt.
  ≈ -9.8 m/s²  →  full left
  ≈ +9.8 m/s²  →  full right
  We map that to the same [-90°, +90°] range the hand tracker uses.
"""

import asyncio
import json
import threading
import math

try:
    import websockets
    _WS_AVAILABLE = True
except ImportError:
    _WS_AVAILABLE = False


class PhoneTracker:
    # How aggressively tilt maps to steering (lower = needs bigger tilt)
    SENSITIVITY = 1.2   # 1.0 = full tilt needed for full lock

    def __init__(self, phone_ip: str, port: int = 8080):
        self.phone_ip = phone_ip
        self.port = port

        self._steering_angle = 0.0
        self._connected = False
        self._error: str | None = None

        # Run the async listener in a background daemon thread
        self._thread = threading.Thread(target=self._run_loop, daemon=True)

    # ── Public API ──────────────────────────────────────────────────────

    def start(self):
        """Start the background WebSocket listener thread."""
        if not _WS_AVAILABLE:
            raise RuntimeError("websockets library not installed. Run: pip install websockets")
        self._thread.start()

    def get_steering(self) -> tuple[float, bool]:
        """
        Returns (steering_angle, is_connected).
        steering_angle is in [-90, +90] — same scale as HandTracker.
        """
        return self._steering_angle, self._connected

    # ── Internal ─────────────────────────────────────────────────────────

    def _run_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._listen_forever())

    async def _listen_forever(self):
        uri = (
            f"ws://{self.phone_ip}:{self.port}"
            f"/sensor/connect?type=android.sensor.accelerometer"
        )
        print(f"[PhoneTracker] Connecting to {uri} …")

        while True:
            try:
                async with websockets.connect(uri, ping_interval=None) as ws:
                    self._connected = True
                    self._error = None
                    print("[PhoneTracker] ✅ Connected! Tilt your phone to steer.")
                    async for raw in ws:
                        self._parse(raw)

            except Exception as exc:
                self._connected = False
                self._error = str(exc)
                print(f"[PhoneTracker] Connection lost ({exc}). Retrying in 2 s …")
                await asyncio.sleep(2)

    def _parse(self, raw: str):
        try:
            data = json.loads(raw)
            values = data.get("values", [])
            if len(values) < 3:
                return

            # values = [x, y, z]  in m/s²
            # X-axis: positive = tilted right, negative = tilted left
            accel_x = values[0]

            # Map ±9.8 m/s² → ±90°  then apply sensitivity
            angle = accel_x * (90.0 / 9.8) * self.SENSITIVITY
            angle = max(-90.0, min(90.0, angle))

            self._steering_angle = angle

        except (json.JSONDecodeError, IndexError, TypeError):
            pass   # malformed packet — just skip it
