FROM nginx:alpine

# Copy custom nginx configuration
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Copy frontend static files
COPY frontend /usr/share/nginx/html

# Replace API base URL so the frontend uses same-origin requests
# (nginx will proxy them to the backend)
RUN sed -i "s|const API_BASE_URL = 'http://localhost:8001';|const API_BASE_URL = '';|" /usr/share/nginx/html/api-client.js
