# Use official lightweight Python image
FROM python:3.11-slim

# set workdir
WORKDIR /app

# copy backend and html into image
COPY backend/ ./backend/
COPY html/ ./html/

# install dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# expose port
EXPOSE 5000

# set the default command
CMD ["python", "backend/app.py"]
