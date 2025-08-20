# 使用Nginx作为基础镜像
FROM nginx:alpine

# 复制HTML文件
COPY templates/*.html /usr/share/nginx/html/

# 复制静态文件，保持/static/路径结构
COPY static/ /usr/share/nginx/html/static/

# 复制templates目录
COPY templates/ /usr/share/nginx/html/templates/

# 使用默认nginx配置

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]