// login.js - ログイン処理

document.addEventListener('DOMContentLoaded', () => {
  // 既にログインしている場合はトップページにリダイレクト
  if (!checkAuth(false)) return;
  
  // ログインフォームの送信イベントを処理
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }
});

/**
 * ログインフォームの送信処理
 * @param {Event} event - フォームイベント
 */
async function handleLogin(event) {
  event.preventDefault();
  
  // メッセージをクリア
  clearMessage();
  
  // フォームデータの取得
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;
  
  // 入力検証
  if (!username || !password) {
    showError('ユーザー名とパスワードを入力してください');
    return;
  }
  
  try {
    // FormDataオブジェクトを作成（OAuth2の仕様に合わせる）
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    // ログインAPIを呼び出す
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: formData
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
      throw new Error(data.detail || 'ログインに失敗しました');
    }
    
    // トークンを保存
    saveTokens(data);
    
    // 成功メッセージを表示
    showSuccess('ログインに成功しました。リダイレクトします...');
    
    // トップページにリダイレクト（少し遅延させる）
    setTimeout(() => {
      window.location.href = 'index.html';
    }, 1500);
    
  } catch (error) {
    console.error('Login Error:', error);
    showError(error.message || 'ログイン処理中にエラーが発生しました');
  }
}
