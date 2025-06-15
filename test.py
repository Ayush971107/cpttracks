from main import get_insurance_codes
import asyncio
if __name__ == "__main__":
    description = "62-year-old female with Type 2 diabetes mellitus returns for routine follow-up. HbA1c today is 8.2%, up from 7.1% three months ago. Patient reports increased stress at work and admits to poor dietary compliance. Blood pressure 145/88. Adjusted metformin dose to 1000mg twice daily and added lisinopril 10mg daily. Referred to diabetes educator."
    print(asyncio.run(get_insurance_codes(description)))
