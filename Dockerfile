# Use an official Python runtime as a parent image
FROM tiangolo/uvicorn-gunicorn:python3.11 as base

# Set the working directory in the container to /app
WORKDIR /app

# Copy the start.sh script and make it executable
COPY app /app
RUN chmod +x /app/start.sh

# Add the current directory contents into the container at /app
ADD . /app


# Make ports 7860 (Gradio) and 8081 (FastAPI) available to the world outside this container
EXPOSE 7860 8081

RUN python install.py

# Run the start.sh script when the container launches
CMD ["./start.sh"]

