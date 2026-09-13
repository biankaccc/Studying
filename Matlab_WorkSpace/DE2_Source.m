% 定义时间范围，确保曲线有足够的长度展示趋势
t = linspace(-2, 1, 1000); 
% 定义箭头间隔：每隔多少个数据点画一个箭头
arrow_interval = 150; 
% 箭头矢量放大倍数（核心：强制放大箭头的指向矢量，确保箭头可见）
arrow_magnify = 50; 

hold on;

% ===================== 1. 绘制四条红色特殊解曲线（带清晰箭头） =====================
% 特殊解1: c1=1, c2=0
x1 = 1*exp(3*t) + 0*exp(t);
y1 = -1*exp(3*t) + 0*exp(t);
plot(x1, y1, 'r-', 'LineWidth', 1.5);
% 循环添加均匀分布的箭头
for pos = arrow_interval:arrow_interval:length(t)-1
    % 计算箭头的x/y方向增量（放大后确保可见）
    dx = (x1(pos+1)-x1(pos)) * arrow_magnify;
    dy = (y1(pos+1)-y1(pos)) * arrow_magnify;
    % 移除Scale参数，仅保留AutoScale='off'和MaxHeadSize（兼容所有MATLAB版本）
    quiver(x1(pos), y1(pos), dx, dy, ...
           'Color', 'r', ...
           'MaxHeadSize', 0.8,...  % 大幅增大箭头头部
           'AutoScale', 'off', ... % 强制关闭自动缩放（关键！）
           'LineWidth', 1.5);   % 加粗箭头杆部
end

% 特殊解2: c1=-1, c2=0
x2 = -1*exp(3*t) + 0*exp(t);
y2 = 1*exp(3*t) + 0*exp(t);
plot(x2, y2, 'r-', 'LineWidth', 1.5);
for pos = arrow_interval:arrow_interval:length(t)-1
    dx = (x2(pos+1)-x2(pos)) * arrow_magnify;
    dy = (y2(pos+1)-y2(pos)) * arrow_magnify;
    quiver(x2(pos), y2(pos), dx, dy, ...
           'Color', 'r', 'MaxHeadSize', 0.8, 'AutoScale', 'off', 'LineWidth', 1.5);
end

% 特殊解3: c1=0, c2=1
x3 = 0*exp(3*t) + 1*exp(t);
y3 = 0*exp(3*t) + 0*exp(t);
plot(x3, y3, 'r-', 'LineWidth', 1.5);
for pos = arrow_interval:arrow_interval:length(t)-1
    dx = (x3(pos+1)-x3(pos)) * arrow_magnify;
    dy = (y3(pos+1)-y3(pos)) * arrow_magnify;
    quiver(x3(pos), y3(pos), dx, dy, ...
           'Color', 'r', 'MaxHeadSize', 0.8, 'AutoScale', 'off', 'LineWidth', 1.5);
end

% 特殊解4: c1=0, c2=-1
x4 = 0*exp(3*t) - 1*exp(t);
y4 = 0*exp(3*t) + 0*exp(t);
plot(x4, y4, 'r-', 'LineWidth', 1.5);
for pos = arrow_interval:arrow_interval:length(t)-1
    dx = (x4(pos+1)-x4(pos)) * arrow_magnify;
    dy = (y4(pos+1)-y4(pos)) * arrow_magnify;
    quiver(x4(pos), y4(pos), dx, dy, ...
           'Color', 'r', 'MaxHeadSize', 0.8, 'AutoScale', 'off', 'LineWidth', 1.5);
end

% ===================== 2. 绘制10条黑色一般解曲线（带清晰箭头） =====================
c_combinations = [
    0.5, 1;    -0.3, 0.8;   0.2, -0.5;   -0.4, -0.7;   0.6, -0.2;
    -0.7, 0.4;  0.3, 0.9;   -0.5, -0.3;  0.8, 0.1;    -0.2, 0.6;
];

for i = 1:size(c_combinations, 1)
    c1 = c_combinations(i, 1);
    c2 = c_combinations(i, 2);
    x = c1*exp(3*t) + c2*exp(t);
    y = -c1*exp(3*t) + 0*exp(t);
    plot(x, y, 'k-', 'LineWidth', 1);
    
    for pos = arrow_interval:arrow_interval:length(t)-1
        dx = (x(pos+1)-x(pos)) * arrow_magnify;
        dy = (y(pos+1)-y(pos)) * arrow_magnify;
        quiver(x(pos), y(pos), dx, dy, ...
               'Color', 'k', 'MaxHeadSize', 0.6, 'AutoScale', 'off', 'LineWidth', 1);
    end
end

% ===================== 3. 图形美化设置 =====================
axis equal; % 等比例坐标轴
xlabel('x'); ylabel('y');
title('源节点解曲线（箭头清晰可见）');
grid on; 
hold off;