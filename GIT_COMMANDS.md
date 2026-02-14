# פקודות Git להעלאת הפרויקט ל-GitHub

## פקודות בסיסיות

### 1. בדיקת סטטוס
```bash
git status
```

### 2. בדיקת remote
```bash
git remote -v
```

### 3. הוספת remote (אם עדיין לא הוגדר)
```bash
git remote add origin https://github.com/idoNadav/Assessment_Python.git
```

### 4. וידוא שאנחנו על main branch
```bash
git branch -M main
```

### 5. Push ל-GitHub
```bash
git push -u origin main
```

## אם יש בעיית Authentication

### אפשרות 1: Personal Access Token (PAT)
1. ליצור PAT ב-GitHub: Settings → Developer settings → Personal access tokens → Tokens (classic)
2. להריץ:
```bash
git push -u origin main
# Username: idoNadav
# Password: [הדבק את ה-PAT כאן]
```

### אפשרות 2: GitHub CLI
```bash
gh auth login
git push -u origin main
```

### אפשרות 3: SSH
```bash
# שנה את ה-URL ל-SSH
git remote set-url origin git@github.com:idoNadav/Assessment_Python.git
git push -u origin main
```

### אפשרות 4: Credential Helper (macOS)
```bash
git config --global credential.helper osxkeychain
git push -u origin main
```

## עדכונים עתידיים

### הוספת שינויים חדשים
```bash
# הוספת כל השינויים
git add .

# או הוספת קבצים ספציפיים
git add path/to/file.py

# יצירת commit
git commit -m "תיאור השינויים"

# Push ל-GitHub
git push
```

## פקודות נוספות שימושיות

### צפייה בהיסטוריה
```bash
git log --oneline
git log --oneline --graph --all
```

### בדיקת ההבדלים
```bash
git diff
git diff --staged
```

### בדיקת branches
```bash
git branch
git branch -a
```

### חזרה ל-commit קודם
```bash
git log --oneline  # למצוא את ה-commit hash
git checkout <commit-hash>
```

### חזרה ל-main
```bash
git checkout main
```

## קישורים שימושיים

- **Repository**: https://github.com/idoNadav/Assessment_Python
- **GitHub Docs**: https://docs.github.com/en/get-started/getting-started-with-git
