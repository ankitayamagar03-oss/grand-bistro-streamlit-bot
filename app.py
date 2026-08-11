import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. Page Header Customization
st.set_page_config(page_title="Grand Bistro Bot", page_icon="🍕")
st.title("🍕 Grand Bistro AI Assistant")
st.markdown("---")

# 2. Initialize Session State Memory Variables
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.booking_data = {}
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Welcome to **The Grand Bistro**! 👋 I can help you secure a table instantly. What name should I put your reservation under?"}
    ]

# Render persistent historical bubbles on reload
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 3. Google Sheets Append Logic Functions
def upload_row_to_sheets(info_dict):
    try:
        # Define API accessibility scope authorizations
        scope = ["https://google.com", "https://googleapis.com"]
        
        # Safely pull credentials mapping dictionaries straight out of Streamlit Cloud environment secrets
        google_creds_dict = st.secrets["gcp_service_account"]
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
        gspread_client = gspread.authorize(credentials)
        
        # Connect explicitly to your spreadsheet workbook and worksheet tab
        workbook = gspread_client.open("Restaurant Bot Database")
        worksheet = workbook.worksheet("Reservations")
        
        # Compile entry row matching database columns: Name, Phone, Guests, Date, Time, Summary
        summary_log = f"Table booking arranged for {info_dict['guests']} guests on {info_dict['date']} at {info_dict['time']} under {info_dict['name']}."
        row_payload = [info_dict['name'], info_dict['phone'], info_dict['guests'], info_dict['date'], info_dict['time'], summary_log]
        
        worksheet.append_row(row_payload)
        return True
    except Exception as network_error:
        st.error(f"Database sync operation failed: {network_error}")
        return False

# 4. Handle Chat Interception Flows
if customer_message := st.chat_input("Write your response here..."):
    # Append the user's text entry to state lists instantly
    st.session_state.chat_history.append({"role": "user", "content": customer_message})
    with st.chat_message("user"):
        st.write(customer_message)

    bot_text = ""

    # Phase Flow-Chart Evaluation Checks
    if st.session_state.step == 1:
        st.session_state.booking_data["name"] = customer_message
        bot_text = f"Thank you, **{customer_message}**! How many guests will be joining your party today?"
        st.session_state.step = 2

    elif st.session_state.step == 2:
        st.session_state.booking_data["guests"] = customer_message
        bot_text = "Understood! What date would you like to request your table for? (e.g., Friday, Aug 15)"
        st.session_state.step = 3

    elif st.session_state.step == 3:
        st.session_state.booking_data["date"] = customer_message
        bot_text = "Perfect. What time works best for your party? (e.g., 7:30 PM)"
        st.session_state.step = 4

    elif st.session_state.step == 4:
        st.session_state.booking_data["time"] = customer_message
        bot_text = "Lastly, please provide your primary phone contact number for validation confirmations:"
        st.session_state.step = 5

    elif st.session_state.step == 5:
        st.session_state.booking_data["phone"] = customer_message
        
        # Trigger background data-syncing scripts safely
        with st.spinner("Logging your booking summary into our restaurant databases..."):
            is_saved = upload_row_to_sheets(st.session_state.booking_data)
        
        if is_saved:
            bot_text = f"🎉 **Reservation Confirmed Successfully!**\n\n Here is your receipt receipt overview:\n\n" \
                       f"• 👤 **Host Name:** {st.session_state.booking_data['name']}\n" \
                       f"• 👥 **Total Guests:** {st.session_state.booking_data['guests']}\n" \
                       f"• 📅 **Date Window:** {st.session_state.booking_data['date']}\n" \
                       f"• ⏰ **Arrival Time:** {st.session_state.booking_data['time']}\n" \
                       f"• 📞 **Contact Phone:** {st.session_state.booking_data['phone']}\n\n" \
                       f"We look forward to serving you spectacular food at The Grand Bistro! See you soon."
        else:
            bot_text = "⚠️ Your booking collection completed, but our logging pipeline timed out. Please contact bistro front desk handlers."
        st.session_state.step = 6  # Stop script updates after data capture terminates

    # Output bot chat container objects into canvas panels
    if bot_text:
        st.session_state.chat_history.append({"role": "assistant", "content": bot_text})
        with st.chat_message("assistant"):
            st.write(bot_text)
