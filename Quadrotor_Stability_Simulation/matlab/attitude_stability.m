% Linear stability of one quadrotor attitude axis (roll) with a PID controller.
% Plant linearised at hover: I * phi_ddot = tau  ->  G(s) = 1 / (I s^2)
% Same gains as quadrotor/controller.py (torque = I * (Kp e + Ki/s e - Kd s phi)).
% Requires the Control System Toolbox.

Ixx = 0.0082;           % kg.m^2
Kp = 144; Ki = 20; Kd = 19;

G  = tf(1, [Ixx 0 0]);              % torque -> roll angle
C  = Ixx * tf([Kd Kp Ki], [1 0]);   % PID scaled by inertia
T  = feedback(C * G, 1);            % closed loop (derivative on error, for analysis)

disp('Closed-loop poles:'); disp(pole(T));
fprintf('Routh-Hurwitz condition Kd*Kp > Ki: %d\n', Kd*Kp > Ki);

figure; step(T, 2); grid on; title('Roll step response (linear model)');
figure; margin(C * G); grid on;      % gain and phase margins
figure; rlocus(G * tf([Kd Kp Ki], [1 0]) * Ixx); title('Root locus vs loop gain');
