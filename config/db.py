from sqlalchemy import create_engine, MetaData

DB_INFO = "mysql+pymysql://admin:turmalrs1234@terraform-20241129194814887300000007.chye8488mdam.us-east-1.rds.amazonaws.com:3306/saudeplusdb"
engine = create_engine(DB_INFO)
conn = engine.connect()



