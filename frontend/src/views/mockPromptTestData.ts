export interface MockOutput {
  runIndex: number
  content: string
  meta?: string
  variables?: Record<string, string>
}

export interface MockUnit {
  id: number
  name: string
  promptVersion: string
  modelName: string
  parameterSet: string
  parameters: Record<string, string | number>
  outputs: MockOutput[]
}

export interface MockSummary {
  taskId: string
  taskName: string
  createdAt: string
}

export const mockSummary: MockSummary = {
  taskId: 'demo',
  taskName: 'Prompt 测试任务（Mock）',
  createdAt: '2025-10-10 12:30'
}

export const mockUnits: MockUnit[] = [
  {
    id: 1,
    name: '单元 A',
    promptVersion: 'v1',
    modelName: 'GPT-4o',
    parameterSet: '参数集 1',
    parameters: {
      温度: 0.7,
      TopP: 0.9,
      最大输出: 512,
      频率惩罚: 0.1
    },
    outputs: [
      {
        runIndex: 1,
        content: 'Hello, how can I assist you today?',
        meta: '耗时 812ms · 25 tokens',
        variables: { text: '你好' }
      },
      {
        runIndex: 2,
        content: 'Hi there! Need any help with PromptWorks?',
        meta: '耗时 790ms · 23 tokens',
        variables: { text: 'PromptWorks 是什么？' }
      },
      {
        runIndex: 3,
        content: 'Hello! I am ready to support your workflow.',
        meta: '耗时 805ms · 24 tokens',
        variables: { text: '请用英文欢迎我' }
      }
    ]
  },
  {
    id: 2,
    name: '单元 B',
    promptVersion: 'v2',
    modelName: 'GPT-4o',
    parameterSet: '参数集 1',
    parameters: {
      温度: 0.6,
      TopP: 0.85,
      最大输出: 512,
      存在惩罚: 0.2
    },
    outputs: [
      {
        runIndex: 1,
        content: '您好，我可以为您提供什么帮助？',
        meta: '耗时 880ms · 29 tokens',
        variables: { text: '你好' }
      },
      {
        runIndex: 2,
        content: '您好！很高兴协助您的 Prompt 设计。',
        meta: '耗时 902ms · 28 tokens',
        variables: { text: 'PromptWorks 是什么？' }
      },
      {
        runIndex: 3,
        content: '你好，我在这里帮你优化提示词流程。',
        meta: '耗时 915ms · 30 tokens',
        variables: { text: '请用英文欢迎我' }
      }
    ]
  },
  {
    id: 3,
    name: '单元 C',
    promptVersion: 'v2',
    modelName: 'Claude 3',
    parameterSet: '参数集 2',
    parameters: {
      温度: 0.5,
      TopP: 0.8,
      最大输出: 1024,
      停止符: '["</response>"]'
    },
    outputs: [
      {
        runIndex: 1,
        content: 'Hello! Happy to help with your prompt workflow.',
        meta: '耗时 1020ms · 27 tokens',
        variables: { text: 'Hello' }
      },
      {
        runIndex: 2,
        content: 'Hi! Let me know how I can support your team.',
        meta: '耗时 1004ms · 26 tokens',
        variables: { text: 'How can I assist?' }
      }
    ]
  }
]
