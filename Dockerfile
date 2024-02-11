# syntax=docker/dockerfile-upstream:master-labs
# Build stage for Tailwind CSS
FROM node:latest as cssbuild
COPY --link --parents lynx/jstoolchain/* /app/
WORKDIR /app/lynx/jstoolchain
RUN npm install
COPY --link --parents  lynx/templates/**/*.html lynx/views/**/*.py lynx/static/lynx/css/input.css /app/
RUN npm run buildcss

# Build stage for Django. All we need from the previous stage is output.css

# 3.10 because background tasks uses `import imp` which isn't supported in 3.12+
FROM python:3.10
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /lynx
COPY --link poetry.lock pyproject.toml .
RUN set -eux \ 
  && echo "Installing dependencies" \
    && pip install poetry --no-cache-dir \
    && poetry install --no-cache --without dev
COPY --link --from=cssbuild /app/lynx/static/lynx/generated/* /lynx/lynx/static/lynx/generated/
COPY . .
RUN set -eux \
  && echo "Collecting static files" \
    && SECRET_KEY=secret poetry run python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["./docker_entrypoint.sh"]
