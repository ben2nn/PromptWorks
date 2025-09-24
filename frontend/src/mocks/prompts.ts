import type { Prompt } from '../types/prompt'

export const mockPrompts: Prompt[] = [
  {
    id: 1,
    name: '销售跟进话术',
    description: '帮助客服在跟进潜在客户时把握需求、传递价值与推进下一步行动。',
    author: '宋佳',
    prompt_class: {
      id: 10,
      name: '客服协助',
      description: '面向客服团队的提示词模板。',
      created_at: '2025-06-01T09:00:00+08:00',
      updated_at: '2025-09-10T12:00:00+08:00'
    },
    current_version: {
      id: 101,
      prompt_id: 1,
      version: 'v1.4.2',
      content: `你是资深销售顾问。
1. 先明确客户当前困扰。
2. 提炼产品价值主张。
3. 给出下一步可执行建议。
保持亲和、循序渐进的语气。`,
      created_at: '2025-09-18T10:20:00+08:00',
      updated_at: '2025-09-18T10:20:00+08:00'
    },
    versions: [
      {
        id: 101,
        prompt_id: 1,
        version: 'v1.4.2',
        content: `你是资深销售顾问。
1. 先明确客户当前困扰。
2. 提炼产品价值主张。
3. 给出下一步可执行建议。
保持亲和、循序渐进的语气。`,
        created_at: '2025-09-18T10:20:00+08:00',
        updated_at: '2025-09-18T10:20:00+08:00'
      },
      {
        id: 96,
        prompt_id: 1,
        version: 'v1.3.0',
        content: `你是一名销售顾问。
1. 询问客户目前的问题。
2. 简要阐述产品优势。
语气保持亲和、简洁。`,
        created_at: '2025-09-10T09:05:00+08:00',
        updated_at: '2025-09-10T09:05:00+08:00'
      },
      {
        id: 71,
        prompt_id: 1,
        version: 'v1.0.0',
        content: '你需要协助销售跟进潜在客户，整理合适的回复要点。',
        created_at: '2025-08-01T14:22:00+08:00',
        updated_at: '2025-08-01T14:22:00+08:00'
      }
    ],
    tags: [
      {
        id: 21,
        name: '销售',
        color: '#409EFF',
        created_at: '2025-06-10T10:00:00+08:00',
        updated_at: '2025-06-10T10:00:00+08:00'
      },
      {
        id: 22,
        name: '中文',
        color: '#67C23A',
        created_at: '2025-06-10T10:00:00+08:00',
        updated_at: '2025-06-10T10:00:00+08:00'
      },
      {
        id: 23,
        name: '对话流程',
        color: '#E6A23C',
        created_at: '2025-06-10T10:00:00+08:00',
        updated_at: '2025-06-10T10:00:00+08:00'
      }
    ],
    created_at: '2025-06-01T09:00:00+08:00',
    updated_at: '2025-09-18T10:20:00+08:00'
  },
  {
    id: 2,
    name: '邮件润色助手',
    description: '优化英文商务邮件语气、结构与措辞，保持专业且友好。',
    author: 'Alex Li',
    prompt_class: {
      id: 11,
      name: '市场传播',
      description: '面向市场、品牌沟通的提示词。',
      created_at: '2025-06-15T11:30:00+08:00',
      updated_at: '2025-08-30T15:12:00+08:00'
    },
    current_version: {
      id: 205,
      prompt_id: 2,
      version: 'v0.9.0',
      content: `You are a senior copy editor.
- Polish greetings and closings.
- Keep sentences concise and respectful.
- Offer two improved alternatives when possible.`,
      created_at: '2025-09-12T08:45:00+08:00',
      updated_at: '2025-09-12T08:45:00+08:00'
    },
    versions: [
      {
        id: 205,
        prompt_id: 2,
        version: 'v0.9.0',
        content: `You are a senior copy editor.
- Polish greetings and closings.
- Keep sentences concise and respectful.
- Offer two improved alternatives when possible.`,
        created_at: '2025-09-12T08:45:00+08:00',
        updated_at: '2025-09-12T08:45:00+08:00'
      },
      {
        id: 184,
        prompt_id: 2,
        version: 'v0.5.0',
        content: `You are a copy editor helping with business emails.
- Make tone polite.
- Check grammar.`,
        created_at: '2025-08-30T15:12:00+08:00',
        updated_at: '2025-08-30T15:12:00+08:00'
      }
    ],
    tags: [
      {
        id: 31,
        name: '英文',
        color: '#F56C6C',
        created_at: '2025-07-01T08:00:00+08:00',
        updated_at: '2025-07-01T08:00:00+08:00'
      },
      {
        id: 32,
        name: '邮件',
        color: '#909399',
        created_at: '2025-07-01T08:00:00+08:00',
        updated_at: '2025-07-01T08:00:00+08:00'
      }
    ],
    created_at: '2025-06-20T09:30:00+08:00',
    updated_at: '2025-09-12T08:45:00+08:00'
  },
  {
    id: 3,
    name: '代码审查要点',
    description: '聚焦性能、安全、可维护性的代码审查策略要求。',
    author: '陈曦',
    prompt_class: {
      id: 12,
      name: '研发效率',
      description: '提升研发流程效率的提示词集合。',
      created_at: '2025-07-05T10:00:00+08:00',
      updated_at: '2025-09-15T09:00:00+08:00'
    },
    current_version: {
      id: 305,
      prompt_id: 3,
      version: 'v2.1.0',
      content: `你是资深代码审查专家。
请重点关注：
1. 性能热点与复杂度。
2. 安全漏洞与数据校验。
3. 代码风格与可维护性。
输出高优先级问题列表并附原因。`,
      created_at: '2025-09-21T14:05:00+08:00',
      updated_at: '2025-09-21T14:05:00+08:00'
    },
    versions: [
      {
        id: 305,
        prompt_id: 3,
        version: 'v2.1.0',
        content: `你是资深代码审查专家。
请重点关注：
1. 性能热点与复杂度。
2. 安全漏洞与数据校验。
3. 代码风格与可维护性。
输出高优先级问题列表并附原因。`,
        created_at: '2025-09-21T14:05:00+08:00',
        updated_at: '2025-09-21T14:05:00+08:00'
      },
      {
        id: 288,
        prompt_id: 3,
        version: 'v2.0.0',
        content: `你是资深代码审查专家。
关注性能、安全、规范三大维度，输出改进建议。`,
        created_at: '2025-09-15T10:30:00+08:00',
        updated_at: '2025-09-15T10:30:00+08:00'
      }
    ],
    tags: [
      {
        id: 41,
        name: '代码质量',
        color: '#36CFC9',
        created_at: '2025-07-10T10:00:00+08:00',
        updated_at: '2025-07-10T10:00:00+08:00'
      },
      {
        id: 42,
        name: '审查',
        color: '#7E5AF5',
        created_at: '2025-07-10T10:00:00+08:00',
        updated_at: '2025-07-10T10:00:00+08:00'
      }
    ],
    created_at: '2025-07-05T10:00:00+08:00',
    updated_at: '2025-09-21T14:05:00+08:00'
  }
]

export function getPromptById(id: number): Prompt | undefined {
  return mockPrompts.find((item) => item.id === id)
}
