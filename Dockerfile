# Build stage for Tailwind CSS
FROM node:latest as cssbuild
COPY . . 
WORKDIR /lynx/jstoolchain
RUN npm install
RUN npm run buildcss

# Build stage for Django. All we need from the previous stage is output.css
FROM python:3
COPY . .
COPY --from=cssbuild /lynx/static/lynx/generated/* ./lynx/static/lynx/generated/
RUN pip install poetry
RUN poetry install

RUN SECRET_KEY=secret poetry run python manage.py collectstatic --noinput
RUN SECRET_KEY=secret CSRF_TRUSTED_ORIGINS=https://localhost poetry run python manage.py migrate --noinput
EXPOSE 8000
CMD ["poetry", "run", "gunicorn", "project_lynx.wsgi:application", "--bind", "0.0.0.0:8000"]
