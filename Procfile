cd /home/muhsil/OneDrive/Documents/college_chatbot
git init
git add .
git commit -m "Initial commit"
# create repo on GitHub manually or:
# gh repo create college_chatbot --public --source=. --push
git remote add origin git@github.com:<your-username>/college_chatbot.git
git branch -M main
git push -u origin main

gh secret set GEMINI_API_KEY --body 'sk_...yourkey...'

web: gunicorn app:app --bind 0.0.0.0:$PORT