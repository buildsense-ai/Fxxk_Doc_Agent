document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const fileInput = document.getElementById('fileInput');
    const fileUploadBtn = document.getElementById('fileUploadBtn');
    const uploadedFilesContainer = document.getElementById('uploadedFiles');
    const filesList = document.getElementById('filesList');
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    const minioStatusText = document.getElementById('minioStatusText');
    const toolCountBadge = document.getElementById('toolCountBadge');
    const toolsList = document.getElementById('toolsList');
    const serverCount = document.getElementById('serverCount');
    const serversList = document.getElementById('serversList');
    const refreshToolsBtn = document.getElementById('refreshTools');
    const typingIndicator = document.getElementById('typingIndicator');
    const togglePanelBtn = document.getElementById('togglePanelBtn');
    const toolsPanel = document.getElementById('toolsPanel');

    let uploadedFiles = []; // To store file objects for the API call

    // --- API Helper ---
    async function apiFetch(endpoint, options = {}) {
        try {
            const response = await fetch(`/api${endpoint}`, options);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: '发生了未知错误' }));
                throw new Error(errorData.error || `HTTP错误! 状态码: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API请求错误 ${endpoint}:`, error);
            showInlineError(error.message);
            throw error;
        }
    }

    // --- Core Functions ---
    async function initializeApp() {
        console.log("正在初始化应用程序...");
        setStatus('connecting', '连接中...');
        try {
            const data = await apiFetch('/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            if (data.success) {
                setStatus('connected', '已连接');
                updateServersUI(data.servers);
                await refreshTools(); // Fetch tools after connecting
            } else {
                setStatus('disconnected', '连接失败');
            }
            await checkMinIOStatus();
        } catch (error) {
            setStatus('disconnected', '连接错误');
        }
    }

    async function sendMessage() {
        const messageText = chatInput.value.trim();
        if (messageText === '') return;

        appendMessage(messageText, 'user-message');
        chatInput.value = '';
        chatInput.disabled = true;
        sendBtn.disabled = true;
        typingIndicator.style.display = 'inline-block';

        // 暂时关闭流式模式，使用普通模式
        const useStreaming = false; // 改为false关闭流式响应

        try {
            if (useStreaming) {
                await sendStreamingMessage(messageText);
            } else {
                await sendRegularMessage(messageText);
            }
        } finally {
            chatInput.disabled = false;
            sendBtn.disabled = false;
            typingIndicator.style.display = 'none';
            chatInput.focus();
        }
    }

    async function sendRegularMessage(messageText) {
        const payload = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: messageText,
                files: uploadedFiles,
            }),
        };
        const data = await apiFetch('/chat', payload);

        if (data.success) {
            appendMessage(data.response, 'system-message', data);
            // Clear uploaded files after successful message send
            uploadedFiles = [];
            updateUploadedFilesUI();
        }
    }

    async function sendStreamingMessage(messageText) {
        // 创建一个容器来显示流式消息
        const streamContainer = document.createElement('div');
        streamContainer.classList.add('message', 'system-message', 'streaming-message');
        streamContainer.innerHTML = `
            <div class="message-icon"><i class="fas fa-robot"></i></div>
            <div class="message-content">
                <div class="thinking-steps"></div>
                <div class="final-answer" style="display: none;"></div>
            </div>
        `;
        
        chatMessages.appendChild(streamContainer);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        const thinkingSteps = streamContainer.querySelector('.thinking-steps');
        const finalAnswer = streamContainer.querySelector('.final-answer');

        try {
            console.log('🔄 开始发送流式请求...');
            const response = await fetch('/api/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: messageText,
                    files: uploadedFiles,
                }),
            });

            if (!response.ok) {
                console.error(`❌ 流式请求失败: ${response.status}`);
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            console.log('✅ 流式请求成功，开始读取数据...');
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let dataCount = 0;

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    console.log('✅ 流式数据读取完成');
                    break;
                }

                buffer += decoder.decode(value, { stream: true });
                
                // 处理完整的数据行
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // 保留最后一行（可能不完整）

                for (const line of lines) {
                    if (line.trim() === '') continue; // 跳过空行
                    
                    console.log(`📡 接收到数据行: ${line}`);
                    
                    if (line.startsWith('data: ')) {
                        try {
                            const jsonStr = line.substring(6);
                            console.log(`📊 解析JSON数据: ${jsonStr}`);
                            const data = JSON.parse(jsonStr);
                            console.log(`✅ 解析成功，类型: ${data.type}`);
                            handleStreamingData(data, thinkingSteps, finalAnswer);
                            dataCount++;
                        } catch (e) {
                            console.error('❌ JSON解析错误:', e, '原始数据:', line);
                        }
                    } else {
                        console.log(`📝 非SSE数据行: ${line}`);
                    }
                }
            }

            console.log(`📊 总共处理了 ${dataCount} 条数据`);
            
            // 清理上传的文件
            uploadedFiles = [];
            updateUploadedFilesUI();

        } catch (error) {
            console.error('❌ 流式响应错误:', error);
            thinkingSteps.innerHTML = `<div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <strong>连接错误:</strong> ${error.message}
            </div>`;
        }
    }

    function handleStreamingData(data, thinkingSteps, finalAnswer) {
        const { type, content, iteration } = data;
        console.log(`🎯 处理流式数据: 类型=${type}, 内容=${content?.substring(0, 50)}...`);

        switch (type) {
            case 'status':
                thinkingSteps.innerHTML += `<div class="step-item status-step">
                    <strong>📡 状态:</strong> ${content}
                </div>`;
                break;

            case 'problem':
                thinkingSteps.innerHTML += `<div class="step-item problem-step">
                    <strong>🎯 问题:</strong> ${content}
                </div>`;
                break;

            case 'iteration':
                thinkingSteps.innerHTML += `<div class="step-item iteration-step">
                    <strong>🔄 ${content}</strong>
                </div>`;
                break;

            case 'thought':
                thinkingSteps.innerHTML += `<div class="step-item thought-step">
                    <strong>💭 Thought:</strong> ${content}
                </div>`;
                break;

            case 'action':
                thinkingSteps.innerHTML += `<div class="step-item action-step">
                    <strong>🔧 Action:</strong> ${content}
                </div>`;
                break;

            case 'action_input':
                thinkingSteps.innerHTML += `<div class="step-item action-input-step">
                    <strong>📝 Action Input:</strong> <pre>${content}</pre>
                </div>`;
                break;

            case 'observation':
                thinkingSteps.innerHTML += `<div class="step-item observation-step">
                    <strong>👀 Observation:</strong> <pre>${content}</pre>
                </div>`;
                break;

            case 'final_answer':
                finalAnswer.style.display = 'block';
                finalAnswer.innerHTML = `<div class="final-answer-content">
                    <strong>✅ Final Answer:</strong>
                    <div>${content.replace(/\[Download(.*?)\]\((.*?)\)/g, `<a href="$2" target="_blank" class="download-link">Download$1</a>`)}</div>
                </div>`;
                break;

            case 'error':
                thinkingSteps.innerHTML += `<div class="step-item error-step">
                    <strong>❌ Error:</strong> ${content}
                </div>`;
                break;

            case 'max_iterations':
                thinkingSteps.innerHTML += `<div class="step-item max-iterations-step">
                    <strong>⚠️ Max Iterations:</strong> ${content}
                </div>`;
                break;
                
            default:
                console.warn(`⚠️ 未知的流式数据类型: ${type}`);
        }

        // 自动滚动到底部
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    async function refreshTools() {
        try {
            const data = await apiFetch('/tools');
            if(data.success) {
                updateToolsUI(data.tools);
            }
        } catch (error) {
            console.error("刷新工具失败");
        }
    }
    
    async function checkMinIOStatus() {
        try {
            const data = await apiFetch('/minio/health');
            minioStatusText.textContent = data.health.status === 'ready' ? 'MinIO: 在线' : 'MinIO: 离线';
            minioStatusText.parentElement.style.color = data.health.status === 'ready' ? '#28a745' : '#dc3545';
        } catch (error) {
             minioStatusText.textContent = 'MinIO: 离线';
             minioStatusText.parentElement.style.color = '#dc3545';
        }
    }

    // --- Panel Toggle Function ---
    function togglePanel() {
        const isCollapsed = toolsPanel.classList.contains('collapsed');
        
        if (isCollapsed) {
            toolsPanel.classList.remove('collapsed');
            togglePanelBtn.classList.add('active');
            togglePanelBtn.innerHTML = '<i class="fas fa-cog"></i><span>工具面板</span>';
        } else {
            toolsPanel.classList.add('collapsed');
            togglePanelBtn.classList.remove('active');
            togglePanelBtn.innerHTML = '<i class="fas fa-cog"></i><span>工具面板</span>';
        }
    }

    // --- Error Handling ---
    function showInlineError(message) {
        // Create error message element
        const errorElement = document.createElement('div');
        errorElement.classList.add('message', 'system-message', 'error-message');
        errorElement.innerHTML = `
            <div class="message-icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="message-content">
                <strong>错误:</strong> ${message}
            </div>
        `;
        
        chatMessages.appendChild(errorElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorElement.parentNode) {
                errorElement.remove();
            }
        }, 5000);
    }
    
    async function handleFileUpload(event) {
        const files = event.target.files;
        if (files.length === 0) return;

        fileUploadBtn.classList.add('uploading');

        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);
            try {
                const data = await apiFetch('/upload', { method: 'POST', body: formData });
                if (data.success) {
                    uploadedFiles.push({
                        name: data.originalName,
                        path: data.filePath,
                        reactAgentPath: data.reactAgentPath,
                        type: data.mimetype,
                    });
                }
            } catch (error) {
                showInlineError(`上传文件 ${file.name} 失败: ${error.message}`);
            }
        }
        
        fileUploadBtn.classList.remove('uploading');
        updateUploadedFilesUI();
        fileInput.value = ''; // Reset file input
    }


    // --- UI Update Functions ---
    function setStatus(status, text) {
        statusIndicator.className = 'status-indicator ' + status;
        statusText.textContent = text;
    }

    function appendMessage(text, type, data = {}) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', type);

        const iconClass = type === 'user-message' ? 'fa-user' : 'fa-robot';
        
        // Use a library like 'marked' in a real app to safely parse markdown
        const processedText = text.replace(/\[Download(.*?)\]\((.*?)\)/g, `<a href="$2" target="_blank" class="download-link">Download$1</a>`);

        messageElement.innerHTML = `
            <div class="message-icon"><i class="fas ${iconClass}"></i></div>
            <div class="message-content">${processedText}</div>
        `;
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function updateToolsUI(tools) {
        toolCountBadge.textContent = tools.length;
        toolsList.innerHTML = '';
        if (tools.length === 0) {
            toolsList.innerHTML = '<div class="list-item-placeholder">暂无可用工具</div>';
            return;
        }
        tools.forEach(tool => {
            const toolElement = document.createElement('div');
            toolElement.classList.add('tool-item');
            toolElement.innerHTML = `
                <span class="tool-name">${tool.name}</span>
                <span class="tool-server">${tool.serverName}</span>
            `;
            toolElement.title = tool.description;
            toolsList.appendChild(toolElement);
        });
    }
    
    function updateServersUI(servers) {
        serverCount.textContent = servers.length;
        serversList.innerHTML = '';
         if (servers.length === 0) {
            serversList.innerHTML = '<div class="list-item-placeholder">暂无配置的服务器</div>';
            return;
        }
        servers.forEach(server => {
            const serverElement = document.createElement('div');
            serverElement.classList.add('server-item');
            serverElement.innerHTML = `
                <div class="server-status-indicator ${server.connected ? 'connected' : ''}"></div>
                <span class="server-name">${server.name}</span>
            `;
            serversList.appendChild(serverElement);
        });
    }

    function updateUploadedFilesUI() {
        filesList.innerHTML = '';
        if (uploadedFiles.length > 0) {
            uploadedFiles.forEach((file, index) => {
                const fileElement = document.createElement('div');
                fileElement.className = 'file-item';
                fileElement.textContent = file.name;
                const removeBtn = document.createElement('button');
                removeBtn.innerHTML = '&times;';
                removeBtn.onclick = () => {
                    uploadedFiles.splice(index, 1);
                    updateUploadedFilesUI();
                };
                fileElement.appendChild(removeBtn);
                filesList.appendChild(fileElement);
            });
            uploadedFilesContainer.style.display = 'block';
        } else {
            uploadedFilesContainer.style.display = 'none';
        }
    }
    
    function showErrorModal(message) {
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorModal').style.display = 'flex';
    }


    // --- Event Listeners ---
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    chatInput.addEventListener('input', () => {
        sendBtn.disabled = chatInput.value.trim() === '' && uploadedFiles.length === 0;
    });

    fileUploadBtn.addEventListener('click', () => fileInput.click());
    togglePanelBtn.addEventListener('click', togglePanel);
    fileInput.addEventListener('change', handleFileUpload);
    
    refreshToolsBtn.addEventListener('click', async () => {
       await initializeApp();
    });

    // --- Init ---
    initializeApp();
});

// For modals
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
} 