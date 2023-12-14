FROM python:3.10.8
WORKDIR /XDash
COPY . /XDash
RUN pip install -r requirements.txt
ENV STREAMLIT_SERVER_PORT=9090
EXPOSE 9090
CMD ["streamlit", "run", "app.py"]
