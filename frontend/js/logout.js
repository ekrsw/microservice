// logout.js - ログアウト処理

document.addEventListener('DOMContentLoaded', () => {
  // ログインしていない場合はログインページにリダイレクト
  if (!checkAuth(true)) return;
  
  // ログアウトボタンのイベントを処理
  const logoutButton = document.getElementById('logoutButton');
  if (logoutButton) {
    logoutButton.addEventListener('click', handleLogout);
  }
  
  // キャンセルボタンのイベントを処理
  const cancelButton = document.getElementById('cancelButton');
  if (cancelButton) {
    cancelButton.addEventListener('click', () => {
      // トップページに戻る
      window.location.href = 'index.html';
    });
  }
});

/**
 * ログアウト処理
 */
async function handleLogout() {
  // メッセージをクリア
  clearMessage();
  
  try {
    // トークンを取得
    const tokens = getTokens();
    if (!tokens || !tokens.refresh_token) {
      throw new Error('ログイン情報が見つかりません');
    }
    
    // ログアウトAPIを呼び出す
    const response = await fetch(`${API_BASE_URL}/logout`, {
      method: 'POST',
      headers: {
        ...DEFAULT_HEADERS,
        'Authorization': `Bearer ${tokens.access_token}`
      },
      body: JSON.stringify({
        refresh_token: tokens.refresh_token
      })
    });
    
    let data;
    try {
      if (response.headers.get('content-type')?.includes('application/json')) {
        data = await response.json();
      } else {
        data = { detail: 'ログアウト処理が完了しました' };
      }
    } catch (e) {
      console.error('JSON parse error:', e);
      data = { detail: 'レスポンスの解析に失敗しました' };
    }
    
    if (!response.ok) {
      throw new Error(data.detail || 'ログアウトに失敗しました');
    }
    
    // ローカルストレージからトークンとユーザー情報を削除
    clearAuth();
    
    // 成功メッセージを表示
    showSuccess('ログアウトしました。ログインページにリダイレクトします...');
    
    // ログインページにリダイレクト（少し遅延させる）
    setTimeout(() => {
      window.location.href = 'login.html';
    }, 1500);
    
  } catch (error) {
    console.error('Logout Error:', error);
    
    // エラーが発生した場合でもローカルストレージをクリア
    clearAuth();
    
    showError(error.message || 'ログアウト処理中にエラーが発生しました');
    
    // エラーが発生した場合でもログインページにリダイレクト
    setTimeout(() => {
      window.location.href = 'login.html';
    }, 2000);
  }
}
