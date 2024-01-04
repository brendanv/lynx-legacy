# Build stage for Tailwind CSS
FROM node:latest as cssbuild
WORKDIR /app
COPY . . 
WORKDIR /app/lynx/jstoolchain
RUN npm install && npm run buildcss

# Build stage for Django. All we need from the previous stage is output.css
FROM python:3
WORKDIR /lynx
COPY . .
COPY --from=cssbuild /app/lynx/static/lynx/generated/* /lynx/lynx/static/lynx/generated/
RUN set -eux \
  && echo "Installing dependencies" \
    && pip install poetry \
    && poetry install \
  && echo "Collecting static files" \
    && SECRET_KEY=secret poetry run python manage.py collectstatic --noinput

# Volume where the sqlite db is stored, so the host device can put it 
# wherever it wants
VOLUME /lynx/data/

EXPOSE 8000
CMD ["./docker_entrypoint.sh"]
