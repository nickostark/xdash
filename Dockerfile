FROM python:3.10.8
WORKDIR /XDash
COPY . /XDash
RUN pip install -r requirements.txt
EXPOSE 8504
CMD ["streamlit", "run", "app.py"]
