FROM nginx:alpine

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy our static files
COPY index.html /usr/share/nginx/html/
COPY styles.css /usr/share/nginx/html/
COPY app.js /usr/share/nginx/html/

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create env-config.js that will be generated at runtime
RUN echo 'window.ENV = { API_URL: "http://localhost:8080" };' > /usr/share/nginx/html/env-config.js

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]