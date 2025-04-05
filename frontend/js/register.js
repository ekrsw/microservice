// register.js - ユーザー登録処理

document.addEventListener('DOMContentLoaded', () => {
  // 既にログインしている場合はトップページにリダイレクト
  if (!checkAuth(false)) return;
  
  // 登録フォームの送信イベントを処理
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    registerForm.addEventListener('submit', handleRegister);
    
    // フォームフィールドのクリック時に内容をクリア
    const usernameField = document.getElementById('username');
    if (usernameField) {
      usernameField.addEventListener('focus', function() {
        if (this.value) {
          const currentValue = this.value;
          this.value = '';
          // フォーカスが外れたときに値が空なら元の値に戻す
          this.addEventListener('blur', function onBlur() {
            if (!this.value) this.value = currentValue;
            this.removeEventListener('blur', onBlur);
          });
        }
      });
    }
  }
});

/**
 * 登録フォームの送信処理
 * @param {Event} event - フォームイベント
 */
async function handleRegister(event) {
  event.preventDefault();
  
  // メッセージをクリア
  clearMessage();
  
  // フォームデータの取得
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;
  const confirmPassword = document.getElementById('confirmPassword').value;
  
  // 入力検証
  if (!username || !password) {
    showError('ユーザー名とパスワードを入力してください');
    return;
  }
  
  if (username.length > 50) {
    showError('ユーザー名は50文字以内で入力してください');
    return;
  }
  
  if (password.length > 16) {
    showError('パスワードは16文字以内で入力してください');
    return;
  }
  
  if (password !== confirmPassword) {
    showError('パスワードと確認用パスワードが一致しません');
    return;
  }
  
  try {
    // 登録APIを呼び出す
    const response = await fetch(`${API_BASE_URL}/register`, {
      method: 'POST',
      headers: DEFAULT_HEADERS,
      body: JSON.stringify({
        username,
        password
      })
    });
    
    let data;
    try {
      data = await response.json();
    } catch (e) {
      console.error('JSON parse error:', e);
      data = { detail: 'レスポンスの解析に失敗しました' };
    }
    
    if (!response.ok) {
      // エラーレスポンスの場合
      throw new Error(data.detail || '登録に失敗しました');
    }
    
    // 成功メッセージを表示
    showSuccess('登録に成功しました。ログインページにリダイレクトします...');
    
    // ログインページにリダイレクト（少し遅延させる）
    setTimeout(() => {
      window.location.href = 'login.html';
    }, 1500);
    
  } catch (error) {
    console.error('Register Error:', error);
    showError(error.message || '登録処理中にエラーが発生しました');
  }
}
