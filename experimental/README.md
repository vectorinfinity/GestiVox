# Experimental glove controller

`Gesture_Controller_Gloved.py` contains an alternate controller that combines
ArUco marker detection, camera calibration, glove segmentation, and tracking.
It is separate from the main MediaPipe controller and is not launched by Proton.

The `calib_images/` directory contains the existing checkerboard samples and
calibration YAML. The controller recalibrates from the checkerboard JPEGs;
`test.yaml` is a reference artifact. Use images from your own camera when
evaluating calibration accuracy.

This prototype uses legacy OpenCV APIs including `Dictionary_get` and
`DetectorParameters_create`. The recorded environment uses OpenCV contrib
4.6.0.66. Newer OpenCV versions may require changes.

The file defines controller classes but has no executable entry point. It is
preserved for development and reference; running it directly does not start
the camera loop. The loop's quit key is **Q** when a developer invokes it.
