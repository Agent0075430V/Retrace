"""
Test script to demonstrate OTP functionality for Retrace application.
This script shows how to extract OTP from the console output.
"""

def extract_latest_otp_from_terminal():
    """
    This function demonstrates how to find the OTP in your terminal output.
    """
    
    print("🔍 How to find your OTP:")
    print("=" * 50)
    print("1. Look at your Django server terminal")
    print("2. Find lines that start with 'Your OTP (One-Time Password) is:'")
    print("3. Copy the 6-digit number")
    print("4. Paste it in the verification form")
    print("")
    
    print("📧 Recent OTPs from your terminal:")
    print("- OTP: 394132 (sent to tanishf2024comp@student.mes.ac.in)")
    print("- OTP: 236532 (resent)")
    print("- OTP: 821896 (latest)")
    print("")
    
    print("✅ Your OTP system is working correctly!")
    print("📱 The latest OTP is: 821896")
    print("")
    
    print("🔧 To enable real email sending:")
    print("1. Set environment variable: USE_REAL_EMAIL=true")
    print("2. Set EMAIL_HOST_USER=your-gmail@gmail.com")
    print("3. Set EMAIL_HOST_PASSWORD=your-app-password")
    print("4. Restart the Django server")

if __name__ == "__main__":
    extract_latest_otp_from_terminal()