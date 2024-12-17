# Use the official Apache Airflow image as the base
FROM apache/airflow:2.10.3

# Switch to root to install additional packages
USER root

COPY requirements.txt /tmp/

# Install the additional Python packages
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Remove the requirements file to keep the image clean
RUN rm /tmp/requirements.txt
RUN python -m nltk.downloader stopwords

# Switch back to the airflow user
USER airflow
