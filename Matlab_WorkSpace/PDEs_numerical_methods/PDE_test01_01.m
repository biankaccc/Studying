clear;clc;
f = @(t,y) -0.5*y;
t0 = 0; y0 = 1;
tend = 1; h = 0.1;
t = t0:h:tend;
N = length(t)-1;

% Euler法
y_euler = zeros(size(t));
y_euler(1) = y0;
for n = 1:N
    y_euler(n+1) = y_euler(n) + h*f(t(n), y_euler(n));
end

% 改进Euler法
y_improved = zeros(size(t));
y_improved(1) = y0;
for n = 1:N
    y_pred = y_improved(n) + h*f(t(n), y_improved(n)); %预测
    y_corr = y_improved(n) + h/2*( f(t(n),y_improved(n)) + f(t(n+1),y_pred) ); %校正
    y_improved(n+1) = y_corr;
end

% 精确解
y_exact = exp(-0.5*t);

% 计算最大误差
err_euler_max = max(abs(y_euler - y_exact));
err_improved_max = max(abs(y_improved - y_exact));
fprintf('Euler最大误差：%.6e\n',err_euler_max);
fprintf('改进Euler最大误差：%.6e\n',err_improved_max);

% 绘图
plot(t,y_euler,'-o', t,y_improved,'-s', t,y_exact,'-k','LineWidth',1);
legend('Euler','改进Euler','精确解 $y=e^{-t/2}$','Interpreter','latex');
xlabel('t'); ylabel('y');
grid on;
title('Euler与改进Euler法对比');