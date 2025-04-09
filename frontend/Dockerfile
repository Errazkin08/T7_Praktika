FROM node:18-alpine as build

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./
# Install all dependencies including dev dependencies
RUN npm install --include=dev

# Copy the rest of the application
COPY . .
# List files for debugging
RUN ls -la 
# Build the application
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]