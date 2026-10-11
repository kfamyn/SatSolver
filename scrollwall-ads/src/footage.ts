// Real app footage used inside the phone close-ups.
//
// To drop in your own recording: put the file in public/footage/, point
// `file` at it and set from/to (seconds). `chimeAt` is the frame (30fps,
// counted from `from`) where the payment chime should land.
export const FOOTAGE = {
  // Unlock sheet "Spend 40 with FocusCard" -> Tilt to spend -> ✓ -> unlocked.
  tiltToSpend: {file: 'footage/app_demo.mp4', from: 15.4, to: 18.8, chimeAt: 76},
};
