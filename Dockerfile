FROM python:3.10.8
WORKDIR /XDash
COPY . /XDash
RUN pip install -r requirements.txt
ENV STREAMLIT_SERVER_PORT=8080
EXPOSE 8080
CMD ["streamlit", "run", "app.py"]
