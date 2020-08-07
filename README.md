## NOWW backend

stack of technology

- [django](https://www.djangoproject.com/) / [django-rest](https://www.django-rest-framework.org/)
- [docker](https://www.docker.com/)
- [jwt](https://jwt.io/)
- [postgresql](https://www.postgresql.org/)
- [redis](https://redis.io/)
- [drf-yasg](https://github.com/axnsan12/drf-yasg)


ci/cd
- [travis-ci](https://travis-ci.org/)

env
- [gcp](https://cloud.google.com/)

# Django config      

```
python manage.py check 
python manage.py makemigrations 
python manage.py migrate

./manage.py createsuperuser

./manage.py drf_create_token admin

```

# SQL db

```
CREATE USER noww_user WITH PASSWORD 'beta.noww';
```

# default swager ui
http://localhost:8000/#/

# docker compose 
- install [docker-compose](https://docs.docker.com/compose/install/)    
- execute ```docker-compose up -d``` to start
- execute ```docker-compose down``` to stop
- if need to rebuild web ```docker-compose up -d --no-deps --build web```

# environment
example for docker usage   
create .env file with 
```
DATABASE_URL=postgres://postgres:beta.noww@localhost:5432/postgres
```
