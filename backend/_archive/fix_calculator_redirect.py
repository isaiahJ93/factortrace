with open('factortrace-frontend/src/app/calculator/page.tsx', 'r') as f:
    content = f.read()

# Remove the redirect
content = content.replace('''setTimeout(() => {
      router.push('/dashboard');
    }, 1500);''', '''// Stay on calculator page
    // router.push('/dashboard');''')

with open('factortrace-frontend/src/app/calculator/page.tsx', 'w') as f:
    f.write(content)

print("✅ Removed auto-redirect from calculator")
