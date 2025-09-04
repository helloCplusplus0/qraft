// Qraft7.0 前端应用脚本

// API基础URL
const API_BASE_URL = '/api';

// 当前选中的模式ID
let currentPatternId = null;

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    // 初始化页面
    initPage();
    
    // 绑定事件处理器
    bindEventHandlers();
});

/**
 * 初始化页面
 */
async function initPage() {
    try {
        // 加载系统概览数据
        await loadOverview();
        
        // 加载数据源和模式类型过滤器
        await loadFilters();
        
        // 加载最新模式
        await loadPatterns();
        
        // 加载最新事件
        await loadEvents();
        
        // 检查系统健康状态
        await checkHealth();
    } catch (error) {
        console.error('初始化页面失败:', error);
        showError('初始化页面失败，请刷新重试');
    }
}

/**
 * 绑定事件处理器
 */
function bindEventHandlers() {
    // 刷新按钮
    document.getElementById('refreshBtn').addEventListener('click', async () => {
        await initPage();
    });
    
    // 数据源过滤器
    document.getElementById('sourceFilter').addEventListener('change', async () => {
        await loadPatterns();
    });
    
    // 模式类型过滤器
    document.getElementById('patternTypeFilter').addEventListener('change', async () => {
        await loadPatterns();
    });
    
    // 反馈按钮
    document.getElementById('positiveFeedback').addEventListener('click', () => {
        submitFeedback(1);
    });
    
    document.getElementById('neutralFeedback').addEventListener('click', () => {
        submitFeedback(0);
    });
    
    document.getElementById('negativeFeedback').addEventListener('click', () => {
        submitFeedback(-1);
    });
}

/**
 * 加载系统概览数据
 */
async function loadOverview() {
    try {
        // 获取事件总数
        const eventsResponse = await fetch(`${API_BASE_URL}/events?limit=1`);
        const eventsData = await eventsResponse.json();
        document.getElementById('eventCount').textContent = eventsData.length > 0 ? eventsData[0].total_count || '--' : '--';
        
        // 获取模式总数
        const patternsResponse = await fetch(`${API_BASE_URL}/patterns?limit=1`);
        const patternsData = await patternsResponse.json();
        document.getElementById('patternCount').textContent = patternsData.length > 0 ? patternsData[0].total_count || '--' : '--';
        
        // 获取数据源数量
        const sourcesResponse = await fetch(`${API_BASE_URL}/sources`);
        const sourcesData = await sourcesResponse.json();
        document.getElementById('sourceCount').textContent = sourcesData.length || '--';
        
        // 获取模式类型数量
        const patternTypesResponse = await fetch(`${API_BASE_URL}/pattern-types`);
        const patternTypesData = await patternTypesResponse.json();
        document.getElementById('patternTypeCount').textContent = patternTypesData.length || '--';
    } catch (error) {
        console.error('加载系统概览失败:', error);
        document.getElementById('eventCount').textContent = '--';
        document.getElementById('patternCount').textContent = '--';
        document.getElementById('sourceCount').textContent = '--';
        document.getElementById('patternTypeCount').textContent = '--';
    }
}

/**
 * 加载过滤器选项
 */
async function loadFilters() {
    try {
        // 加载数据源
        const sourcesResponse = await fetch(`${API_BASE_URL}/sources`);
        const sourcesData = await sourcesResponse.json();
        
        const sourceFilter = document.getElementById('sourceFilter');
        sourceFilter.innerHTML = '<option value="">所有数据源</option>';
        
        sourcesData.forEach(source => {
            const option = document.createElement('option');
            option.value = source.name;
            option.textContent = source.name;
            sourceFilter.appendChild(option);
        });
        
        // 加载模式类型
        const patternTypesResponse = await fetch(`${API_BASE_URL}/pattern-types`);
        const patternTypesData = await patternTypesResponse.json();
        
        const patternTypeFilter = document.getElementById('patternTypeFilter');
        patternTypeFilter.innerHTML = '<option value="">所有模式类型</option>';
        
        patternTypesData.forEach(type => {
            const option = document.createElement('option');
            option.value = type.name;
            option.textContent = type.name;
            patternTypeFilter.appendChild(option);
        });
    } catch (error) {
        console.error('加载过滤器失败:', error);
    }
}

/**
 * 加载最新模式
 */
async function loadPatterns() {
    try {
        const sourceFilter = document.getElementById('sourceFilter').value;
        const patternTypeFilter = document.getElementById('patternTypeFilter').value;
        
        let url = `${API_BASE_URL}/patterns?limit=10`;
        if (sourceFilter) {
            url += `&source=${encodeURIComponent(sourceFilter)}`;
        }
        if (patternTypeFilter) {
            url += `&pattern_type=${encodeURIComponent(patternTypeFilter)}`;
        }
        
        const response = await fetch(url);
        const patterns = await response.json();
        
        const patternTable = document.getElementById('patternTable');
        
        if (patterns.length === 0) {
            patternTable.innerHTML = '<tr><td colspan="7" class="text-center">暂无数据</td></tr>';
            return;
        }
        
        patternTable.innerHTML = '';
        
        patterns.forEach(pattern => {
            const row = document.createElement('tr');
            
            // 格式化时间
            const timestamp = new Date(pattern.timestamp);
            const formattedTime = timestamp.toLocaleString();
            
            // 获取置信度
            const confidence = pattern.details && pattern.details.confidence !== undefined
                ? pattern.details.confidence
                : 0.5;
            
            // 截断说明文本
            const explanation = pattern.explanation || '无说明';
            const shortExplanation = explanation.length > 50
                ? explanation.substring(0, 50) + '...'
                : explanation;
            
            row.innerHTML = `
                <td>${pattern.pattern_id.substring(0, 8)}...</td>
                <td>${formattedTime}</td>
                <td>${pattern.source}</td>
                <td>${pattern.type}</td>
                <td>
                    <div class="confidence-indicator">
                        <div class="confidence-bar" style="width: ${confidence * 100}%"></div>
                    </div>
                    ${(confidence * 100).toFixed(0)}%
                </td>
                <td>${shortExplanation}</td>
                <td>
                    <button class="btn btn-sm btn-primary view-pattern" data-pattern-id="${pattern.pattern_id}">
                        <i class="bi bi-eye"></i>
                    </button>
                </td>
            `;
            
            patternTable.appendChild(row);
        });
        
        // 绑定查看模式详情事件
        document.querySelectorAll('.view-pattern').forEach(button => {
            button.addEventListener('click', async (event) => {
                const patternId = event.currentTarget.getAttribute('data-pattern-id');
                await showPatternDetail(patternId);
            });
        });
    } catch (error) {
        console.error('加载模式失败:', error);
        document.getElementById('patternTable').innerHTML = '<tr><td colspan="7" class="text-center">加载失败</td></tr>';
    }
}

/**
 * 加载最新事件
 */
async function loadEvents() {
    try {
        const response = await fetch(`${API_BASE_URL}/events?limit=10`);
        const events = await response.json();
        
        const eventTable = document.getElementById('eventTable');
        
        if (events.length === 0) {
            eventTable.innerHTML = '<tr><td colspan="4" class="text-center">暂无数据</td></tr>';
            return;
        }
        
        eventTable.innerHTML = '';
        
        events.forEach(event => {
            const row = document.createElement('tr');
            
            // 格式化时间
            const timestamp = new Date(event.timestamp);
            const formattedTime = timestamp.toLocaleString();
            
            row.innerHTML = `
                <td>${event.event_id.substring(0, 8)}...</td>
                <td>${formattedTime}</td>
                <td>${event.source}</td>
                <td>${event.type}</td>
            `;
            
            eventTable.appendChild(row);
        });
    } catch (error) {
        console.error('加载事件失败:', error);
        document.getElementById('eventTable').innerHTML = '<tr><td colspan="4" class="text-center">加载失败</td></tr>';
    }
}

/**
 * 检查系统健康状态
 */
async function checkHealth() {
    try {
        const response = await fetch('/health');
        const health = await response.json();
        
        const healthStatus = document.getElementById('healthStatus');
        healthStatus.innerHTML = '';
        
        // 系统整体状态
        const statusClass = health.status === 'healthy' ? 'status-healthy' : 
                           health.status === 'unhealthy' ? 'status-unhealthy' : 'status-unknown';
        
        const statusDiv = document.createElement('div');
        statusDiv.className = 'mb-3';
        statusDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <span class="status-indicator ${statusClass}"></span>
                <strong>系统状态: ${health.status === 'healthy' ? '正常' : 
                                  health.status === 'unhealthy' ? '异常' : '未知'}</strong>
            </div>
        `;
        
        healthStatus.appendChild(statusDiv);
        
        // 组件状态
        if (health.components) {
            const componentsDiv = document.createElement('div');
            componentsDiv.innerHTML = '<h6 class="mb-2">组件状态:</h6>';
            
            for (const [name, component] of Object.entries(health.components)) {
                const componentClass = component.status === 'healthy' ? 'status-healthy' : 
                                      component.status === 'unhealthy' ? 'status-unhealthy' : 'status-unknown';
                
                const componentDiv = document.createElement('div');
                componentDiv.className = 'ms-3 mb-2';
                componentDiv.innerHTML = `
                    <div class="d-flex align-items-center">
                        <span class="status-indicator ${componentClass}"></span>
                        <div>
                            <div>${name}</div>
                            <small class="text-muted">${component.message}</small>
                        </div>
                    </div>
                `;
                
                componentsDiv.appendChild(componentDiv);
            }
            
            healthStatus.appendChild(componentsDiv);
        }
    } catch (error) {
        console.error('检查健康状态失败:', error);
        document.getElementById('healthStatus').innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle me-2"></i>
                无法获取系统健康状态
            </div>
        `;
    }
}

/**
 * 显示模式详情
 * @param {string} patternId - 模式ID
 */
async function showPatternDetail(patternId) {
    try {
        currentPatternId = patternId;
        
        const patternDetail = document.getElementById('patternDetail');
        patternDetail.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
        
        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('patternModal'));
        modal.show();
        
        // 获取模式详情
        const response = await fetch(`${API_BASE_URL}/patterns/${patternId}`);
        const pattern = await response.json();
        
        // 格式化时间
        const timestamp = new Date(pattern.timestamp);
        const formattedTime = timestamp.toLocaleString();
        
        // 获取置信度
        const confidence = pattern.details && pattern.details.confidence !== undefined
            ? pattern.details.confidence
            : 0.5;
        
        // 构建详情HTML
        let detailHtml = `
            <div class="pattern-detail-section">
                <h6>基本信息</h6>
                <div class="pattern-detail-item">
                    <div class="pattern-detail-label">ID:</div>
                    <div class="pattern-detail-value">${pattern.pattern_id}</div>
                </div>
                <div class="pattern-detail-item">
                    <div class="pattern-detail-label">时间:</div>
                    <div class="pattern-detail-value">${formattedTime}</div>
                </div>
                <div class="pattern-detail-item">
                    <div class="pattern-detail-label">数据源:</div>
                    <div class="pattern-detail-value">${pattern.source}</div>
                </div>
                <div class="pattern-detail-item">
                    <div class="pattern-detail-label">类型:</div>
                    <div class="pattern-detail-value">${pattern.type}</div>
                </div>
                <div class="pattern-detail-item">
                    <div class="pattern-detail-label">置信度:</div>
                    <div class="pattern-detail-value">
                        <div class="confidence-indicator" style="width: 100%">
                            <div class="confidence-bar" style="width: ${confidence * 100}%"></div>
                        </div>
                        ${(confidence * 100).toFixed(0)}%
                    </div>
                </div>
            </div>
        `;
        
        // 添加说明
        if (pattern.explanation) {
            detailHtml += `
                <div class="pattern-detail-section">
                    <h6>说明</h6>
                    <div class="alert alert-info">
                        ${pattern.explanation}
                    </div>
                </div>
            `;
        }
        
        // 添加详情
        if (pattern.details && Object.keys(pattern.details).length > 0) {
            detailHtml += `
                <div class="pattern-detail-section">
                    <h6>详细信息</h6>
            `;
            
            for (const [key, value] of Object.entries(pattern.details)) {
                if (key !== 'confidence') {
                    detailHtml += `
                        <div class="pattern-detail-item">
                            <div class="pattern-detail-label">${key}:</div>
                            <div class="pattern-detail-value">${JSON.stringify(value)}</div>
                        </div>
                    `;
                }
            }
            
            detailHtml += `</div>`;
        }
        
        // 添加贡献因子
        if (pattern.contributors && pattern.contributors.length > 0) {
            detailHtml += `
                <div class="pattern-detail-section">
                    <h6>贡献因子</h6>
            `;
            
            pattern.contributors.forEach(contributor => {
                detailHtml += `
                    <div class="contributor-item">
                        <div class="contributor-field">${contributor.field}</div>
                        <div class="contributor-bar">
                            <div class="contributor-bar-fill" style="width: ${contributor.score * 100}%"></div>
                        </div>
                        <div class="contributor-score">${(contributor.score * 100).toFixed(0)}%</div>
                    </div>
                `;
            });
            
            detailHtml += `</div>`;
        }
        
        patternDetail.innerHTML = detailHtml;
    } catch (error) {
        console.error('加载模式详情失败:', error);
        document.getElementById('patternDetail').innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle me-2"></i>
                加载模式详情失败
            </div>
        `;
    }
}

/**
 * 提交模式反馈
 * @param {number} rating - 评分 (-1, 0, 1)
 */
async function submitFeedback(rating) {
    if (!currentPatternId) {
        return;
    }
    
    try {
        const comment = document.getElementById('feedbackComment').value;
        
        const response = await fetch(`${API_BASE_URL}/patterns/${currentPatternId}/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: 'web-user',
                rating: rating,
                comment: comment
            })
        });
        
        if (response.ok) {
            // 清空评论
            document.getElementById('feedbackComment').value = '';
            
            // 显示成功消息
            alert('反馈提交成功');
        } else {
            throw new Error('提交失败');
        }
    } catch (error) {
        console.error('提交反馈失败:', error);
        alert('提交反馈失败，请重试');
    }
}

/**
 * 显示错误消息
 * @param {string} message - 错误消息
 */
function showError(message) {
    alert(message);
}