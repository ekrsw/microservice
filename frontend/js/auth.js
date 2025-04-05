// auth.js - 認証関連の共通関数

// APIのベースURL
const API_BASE_URL = 'http://localhost:80/api/v1/auth';

// CORSの問題を回避するためのヘッダー
const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json'
};

// ローカルストレージのキー
const TOKEN_KEY = 'auth_tokens';
const USER_KEY = 'user_info';

/**
 * トークンをローカルストレージに保存する
 * @param {Object} tokens - アクセストークンとリフレッシュトークンを含むオブジェクト
 */
function saveTokens(tokens) {
  localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
}

/**
 * ローカルストレージからトークンを取得する
 * @returns {Object|null} トークンオブジェクトまたはnull
 */
function getTokens() {
  const tokens = localStorage.getItem(TOKEN_KEY);
  return tokens ? JSON.parse(tokens) : null;
}

/**
 * ユーザー情報をローカルストレージに保存する
 * @param {Object} user - ユーザー情報オブジェクト
 */
function saveUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * ローカルストレージからユーザー情報を取得する
 * @returns {Object|null} ユーザー情報オブジェクトまたはnull
 */
function getUser() {
  const user = localStorage.getItem(USER_KEY);
  return user ? JSON.parse(user) : null;
}

/**
 * ローカルストレージからトークンとユーザー情報を削除する
 */
function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * ユーザーがログインしているかどうかを確認する
 * @returns {boolean} ログイン状態
 */
function isLoggedIn() {
  return !!getTokens();
}

/**
 * ログイン状態に応じてリダイレクトする
 * @param {boolean} requireAuth - 認証が必要かどうか
 */
function checkAuth(requireAuth = true) {
  const loggedIn = isLoggedIn();
  
  if (requireAuth && !loggedIn) {
    // 認証が必要なのにログインしていない場合はログインページへ
    window.location.href = '/frontend/login.html';
    return false;
  } else if (!requireAuth && loggedIn) {
    // 認証が不要なのにログインしている場合はトップページへ
    window.location.href = '/frontend/index.html';
    return false;
  }
  
  return true;
}

/**
 * APIリクエストを送信する
 * @param {string} endpoint - エンドポイント
 * @param {Object} options - フェッチオプション
 * @returns {Promise<Object>} レスポンスデータ
 */
async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  // デフォルトのヘッダーを設定
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };
  
  // 認証が必要な場合はトークンを追加
  const tokens = getTokens();
  if (tokens && tokens.access_token) {
    headers['Authorization'] = `Bearer ${tokens.access_token}`;
  }
  
  try {
    const response = await fetch(url, {
      ...options,
      headers
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      // エラーレスポンスの場合
      throw new Error(data.detail || 'APIリクエストエラー');
    }
    
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

/**
 * エラーメッセージを表示する
 * @param {string} message - エラーメッセージ
 * @param {string} elementId - メッセージを表示する要素のID
 */
function showError(message, elementId = 'message') {
  const messageElement = document.getElementById(elementId);
  if (messageElement) {
    messageElement.className = 'message error';
    messageElement.textContent = message;
    messageElement.style.display = 'block';
  }
}

/**
 * 成功メッセージを表示する
 * @param {string} message - 成功メッセージ
 * @param {string} elementId - メッセージを表示する要素のID
 */
function showSuccess(message, elementId = 'message') {
  const messageElement = document.getElementById(elementId);
  if (messageElement) {
    messageElement.className = 'message success';
    messageElement.textContent = message;
    messageElement.style.display = 'block';
  }
}

/**
 * メッセージをクリアする
 * @param {string} elementId - メッセージ要素のID
 */
function clearMessage(elementId = 'message') {
  const messageElement = document.getElementById(elementId);
  if (messageElement) {
    messageElement.style.display = 'none';
    messageElement.textContent = '';
  }
}

// ページ読み込み時に実行する共通処理
document.addEventListener('DOMContentLoaded', () => {
  // ナビゲーションの更新
  updateNavigation();
});

/**
 * ログイン状態に応じてナビゲーションを更新する
 */
function updateNavigation() {
  const navElement = document.querySelector('.nav');
  if (!navElement) return;
  
  if (isLoggedIn()) {
    // ログイン中の場合
    navElement.innerHTML = `
      <a href="/frontend/index.html">ホーム</a>
      <a href="/frontend/logout.html">ログアウト</a>
    `;
  } else {
    // 未ログインの場合
    navElement.innerHTML = `
      <a href="/frontend/login.html">ログイン</a>
      <a href="/frontend/register.html">新規登録</a>
    `;
  }
}
