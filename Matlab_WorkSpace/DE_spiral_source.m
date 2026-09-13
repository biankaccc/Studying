% ========== 1. 全区域加密网格（原点无真空） ==========
[x, y] = meshgrid(-4:0.15:4, -4:0.15:4);  % 平衡密度与运行速度

% ========== 2. 微分方程：虚部=8，实部=2（保证发散+螺旋清晰） ==========
% 特征值：λ=2±8i（实部>0=螺旋源，虚部=8=螺旋密集但可展开）
dx_dt = 2*x - 8*y;
dy_dt = 8*x + 2*y;

% 单位归一化+适配显示（全版本兼容）
mag = sqrt(dx_dt.^2 + dy_dt.^2);
mag(mag < 1e-6) = 1;  % 原点处避免除零
dx_unit = dx_dt ./ mag * 0.2;   % 放大速度场，方向更清晰
dy_unit = dy_dt ./ mag * 0.2;

% ========== 3. 绘制黑色速度场（保留箭头展示方向） ==========
figure('Color','w','Position',[100,100,1000,800]);
quiver(x, y, dx_unit, dy_unit, 'Color','k', 'MaxHeadSize',0.3, 'LineWidth',1);
hold on;

% ========== 4. 解曲线：适配虚部=8的参数（从原点展开不缩点） ==========
dfun = @(t,z) [2*z(1)-8*z(2); 8*z(1)+2*z(2)];
tspan = linspace(0, 1.5, 2500);  % 时间适配8倍虚部，展示2-3圈螺旋
z0 = [0.3; 0];  % 初始值贴近原点（0.3），确保快速展开不缩点
[~, z_sol] = ode45(dfun, tspan, z0);
x_sol = z_sol(:,1);
y_sol = z_sol(:,2);

% ========== 5. 绘制红色螺旋线（加粗+抗锯齿，确保可见） ==========
plot(x_sol, y_sol, 'r-', 'LineWidth', 2.8, 'LineSmoothing','on');

% ========== 6. 标记原点和螺旋起点（明确起始位置） ==========
plot(0, 0, 'ko', 'MarkerSize', 7, 'MarkerFaceColor', 'k');  % 黑色原点标记
plot(x_sol(1), y_sol(1), 'ro', 'MarkerSize', 5, 'MarkerFaceColor', 'r');  % 红色起点（贴近原点）

% ========== 7. 视觉优化：适配虚部=8的螺旋形态 ==========
axis equal;
xlim([-4 4]); ylim([-4 4]);
xlabel('x (unit)'); ylabel('y (unit)');
title('螺旋源相图（虚部=8，红色螺旋线从原点出发清晰可见）');
grid on;
hold off;