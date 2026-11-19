/**
 * BFS & DFS 미로 탈출(Maze Escape) 시각화 및 비교 분석 GAS 웹 애플리케이션
 * 파일: Code.gs
 */

function doGet(e) {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('BFS vs DFS 미로 탈출 벤치마커 (Queue vs Stack)')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1.0')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * Cloud Run 백엔드(main.py)로 미로 탐색(BFS vs DFS 동시 비교) 요청
 * @param {string} serverUrl - Cloud Run 서버 URL (예: https://my-cloudrun-app-xxxxx.run.app)
 * @param {Object} mazeData - { grid: number[][], start: [r, c], goal: [r, c], algorithm: "BOTH" }
 * @return {Object} 서버 응답 데이터
 */
function fetchMazeComparison(serverUrl, mazeData) {
  try {
    if (!serverUrl || typeof serverUrl !== 'string') {
      throw new Error('유효한 Cloud Run 서버 URL을 입력해 주세요.');
    }

    var endpoint = serverUrl.replace(/\/+$/, '') + '/maze/compare';
    var payload = JSON.stringify(mazeData);

    var options = {
      method: 'post',
      contentType: 'application/json',
      payload: payload,
      muteHttpExceptions: true
    };

    var response = UrlFetchApp.fetch(endpoint, options);
    var statusCode = response.getResponseCode();
    var content = response.getContentText();

    if (statusCode >= 200 && statusCode < 300) {
      return { success: true, data: JSON.parse(content) };
    } else {
      var errDetail = '서버 응답 오류 (HTTP ' + statusCode + ')';
      try {
        var jsonErr = JSON.parse(content);
        if (jsonErr.detail) errDetail += ': ' + jsonErr.detail;
      } catch (e) {
        errDetail += ': ' + content;
      }
      return { success: false, error: errDetail };
    }
  } catch (error) {
    return { success: false, error: error.toString() };
  }
}

/**
 * Cloud Run 백엔드로 일반 그래프 탐색 요청 (기존 호환성)
 * @param {string} serverUrl - Cloud Run 서버 URL
 * @param {Object} graphData - { nodes: [...], edges: [...], start_node: "...", algorithm: "BFS" | "DFS" }
 * @return {Object} 서버 응답 데이터
 */
function fetchTraversalData(serverUrl, graphData) {
  try {
    if (!serverUrl || typeof serverUrl !== 'string') {
      throw new Error('유효한 Cloud Run 서버 URL을 입력해 주세요.');
    }

    var endpoint = serverUrl.replace(/\/+$/, '') + '/traverse';
    var payload = JSON.stringify(graphData);

    var options = {
      method: 'post',
      contentType: 'application/json',
      payload: payload,
      muteHttpExceptions: true
    };

    var response = UrlFetchApp.fetch(endpoint, options);
    var statusCode = response.getResponseCode();
    var content = response.getContentText();

    if (statusCode >= 200 && statusCode < 300) {
      return { success: true, data: JSON.parse(content) };
    } else {
      var errDetail = '서버 오류 (HTTP ' + statusCode + ')';
      try {
        var jsonErr = JSON.parse(content);
        if (jsonErr.detail) errDetail += ': ' + jsonErr.detail;
      } catch (e) {
        errDetail += ': ' + content;
      }
      return { success: false, error: errDetail };
    }
  } catch (error) {
    return { success: false, error: error.toString() };
  }
}
