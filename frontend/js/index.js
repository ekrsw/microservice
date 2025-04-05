// index.js - トップページの処理

document.addEventListener('DOMContentLoaded', () => {
  // ログインしていない場合はログインページにリダイレクト
  if (!checkAuth(true)) return;
  
  // ユーザー情報を表示
  displayUserInfo();
});

/**
 * ユーザー情報を表示する
 */
async function displayUserInfo() {
  const userInfoElement = document.getElementById('userInfo');
  if (!userInfoElement) return;
  
  try {
    // トークンを取得
    const tokens = getTokens();
    if (!tokens || !tokens.access_token) {
      throw new Error('ログイン情報が見つかりません');
    }
    
    // JWTからユーザーIDを取得
    const payload = parseJwt(tokens.access_token);
    if (!payload || !payload.sub) {
      throw new Error('トークンが無効です');
    }
    
    // ユーザー情報を表示
    userInfoElement.innerHTML = `
      <p><strong>ログイン状態:</strong> ログイン中</p>
      <p><strong>ユーザーID:</strong> ${payload.sub}</p>
      <p><strong>トークン有効期限:</strong> ${new Date(payload.exp * 1000).toLocaleString()}</p>
    `;
    
  } catch (error) {
    console.error('User Info Error:', error);
    userInfoElement.innerHTML = `
      <p>ユーザー情報の取得に失敗しました</p>
      <p>エラー: ${error.message}</p>
    `;
  }
}

/**
 * JWT（JSON Web Token）をデコードしてペイロードを取得する
 * @param {string} token - JWTトークン
 * @returns {Object|null} デコードされたペイロードまたはnull
 */
function parseJwt(token) {
  try {
    // トークンの中間部分（ペイロード）を取得
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    
    // Base64デコード
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('JWT Parse Error:', error);
    return null;
  }
}
