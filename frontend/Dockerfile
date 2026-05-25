FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
# Use npm install (not npm ci) so platform-specific optional deps like
# @emnapi/* on linux/arm64 resolve cleanly when the lock was generated on macOS.
RUN npm install --no-audit --no-fund --include=optional
COPY . .
RUN npx ng build --configuration production

FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
