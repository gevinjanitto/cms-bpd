FROM node:20-alpine AS build
WORKDIR /app
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL GENERATE_SOURCEMAP=false CI=true
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile --network-timeout 600000
COPY . .
RUN yarn build

FROM node:20-alpine
WORKDIR /app
RUN yarn global add serve@14.2.4
COPY --from=build /app/build ./build
ENV PORT=3000
EXPOSE 3000
CMD ["sh", "-c", "serve -s build -l tcp://0.0.0.0:${PORT}"]
