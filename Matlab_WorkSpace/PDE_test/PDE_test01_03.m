%% 第3题 Euler / 改进Euler / RK4
clear;clc;
f = @(x,y) y - 2*x/y;
h = 1/16;
x0 = 0; y0 = 1;
x_end = 1;
x = x0:h:x_end;
n = length(x);

y_euler = zeros(1,n);
y_improved = zeros(1,n);
y_rk4 = zeros(1,n);

y_euler(1)=y0;
y_improved(1)=y0;
y_rk4(1)=y0;

for i=1:n-1
    % Euler
    y_euler(i+1) = y_euler(i) + h*f(x(i), y_euler(i));
    
    % 改进Euler
    yp = y_improved(i) + h*f(x(i), y_improved(i));
    yc = y_improved(i) + h*f(x(i+1), yp);
    y_improved(i+1) = (yp+yc)/2;
    
    % RK4 四阶龙格库塔
    K1 = f(x(i), y_rk4(i));
    K2 = f(x(i)+h/2, y_rk4(i)+h/2*K1);
    K3 = f(x(i)+h/2, y_rk4(i)+h/2*K2);
    K4 = f(x(i)+h, y_rk4(i)+h*K3);
    y_rk4(i+1) = y_rk4(i) + h/6*(K1 + 2*K2 + 2*K3 + K4);
end

y_exact = sqrt(1+2*x);

figure(2);
plot(x,y_euler,'r-o',x,y_improved,'g-*',x,y_rk4,'m-s',x,y_exact,'b-');
lgd = legend('Euler','改进Euler','RK4','精确解 sqrt{1+2x}');
xlabel('x');ylabel('y');title('第3题 h=1/16 数值方法对比');
grid on;

% 输出误差
fprintf('Euler最大误差：%.4e\n',max(abs(y_euler-y_exact)));
fprintf('改进Euler最大误差：%.4e\n',max(abs(y_improved-y_exact)));
fprintf('RK4最大误差：%.4e\n',max(abs(y_rk4-y_exact)));

