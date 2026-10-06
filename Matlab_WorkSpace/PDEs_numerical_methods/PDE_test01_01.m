%% 第1题 Euler法 & 改进Euler法
clear;clc;
f = @(x,y) 0.5*x;
h = 0.1;
x0 = 0; y0 = 0;
x_end = 1;
x = x0:h:x_end;
n = length(x);

y_euler = zeros(1,n);
y_improved = zeros(1,n);
y_euler(1)=y0;
y_improved(1)=y0;

for i = 1:n-1
    % Euler
    y_euler(i+1) = y_euler(i) + h*f(x(i), y_euler(i));
    % 改进Euler（预估校正）
    yp = y_improved(i) + h*f(x(i), y_improved(i));
    yc = y_improved(i) + h*f(x(i+1), yp);
    y_improved(i+1) = (yp + yc)/2;
end

y_exact = 0.25*x.^2;    % 方程真实解析解

figure(1);
plot(x,y_euler,'r-o',x,y_improved,'g-*',x,y_exact,'b-');
legend('Euler','改进Euler','真实解析解y=0.25x^2');
xlabel('x');ylabel('y');title('第1题 数值解对比 h=0.1');
grid on;
