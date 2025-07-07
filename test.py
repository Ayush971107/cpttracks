from main import get_insurance_codes
import asyncio
if __name__ == "__main__":
    description = "This patient presents with acute onset of fever, malaise, and localized erythema with purulent drainage from the left lower extremity. Blood cultures and wound swab were obtained, confirming methicillin-resistant Staphylococcus aureus (MRSA). Initiated intravenous vancomycin and monitored for systemic involvement. Documentation includes diagnostic confirmation, antimicrobial selection rationale, and monitoring for adverse reactions and clinical improvement. Infection control precautions implemented per hospital protoco"
    print(asyncio.run(get_insurance_codes(description)))
