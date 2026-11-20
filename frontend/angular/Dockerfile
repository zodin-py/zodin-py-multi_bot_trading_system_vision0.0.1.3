FROM node:22-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache python3 make g++ 2>/dev/null || true

# Copy package files and install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy Angular source code
COPY src/ ./src/
COPY angular.json ./
COPY tailwind.config.cjs ./
COPY postcss.config.cjs ./

# Build Angular application
RUN npm run build

# Production stage - serve with nginx or serve static files
FROM nginx:alpine AS production

# Copy built assets from builder
COPY --from=builder /app/dist/ /usr/share/nginx/html/

# Expose port 80 for nginx
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]