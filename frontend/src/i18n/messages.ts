export const messages = {
  'zh-CN': {
    common: {
      notSet: '未设置',
      cancel: '取消',
      confirm: '确认',
      delete: '删除',
      submit: '提交',
      save: '保存',
      create: '新建',
      edit: '编辑',
      descriptionNone: '暂无描述',
      notEnabled: '未启用'
    },
    app: {
      title: 'PromptWorks 控制台',
      settings: '设置',
      languageCn: '中文',
      languageEn: 'English',
      themeDark: '深色模式'
    },
    menu: {
      prompt: 'Prompt 管理',
      quickTest: '快速测试',
      testJob: '测试任务',
      class: '分类管理',
      tag: '标签管理',
      llm: 'LLMs 管理',
      usage: '用量管理'
    },
    promptManagement: {
      headerTitle: 'Prompt 管理',
      headerDescription: '集中管理提示词资产，快速检索分类、标签与作者信息。',
      createPrompt: '新建 Prompt',
      allClasses: '全部分类',
      searchPlaceholder: '搜索标题 / 内容 / 作者',
      tagPlaceholder: '选择标签筛选',
      sortPlaceholder: '排序方式',
      sortDefault: '默认排序',
      sortCreatedAt: '按创建时间',
      sortUpdatedAt: '按更新时间',
      sortAuthor: '按作者',
      currentVersion: '当前版本',
      author: '作者',
      createdAt: '创建时间',
      updatedAt: '更新时间',
      confirmDelete: '确认删除「{name}」吗？',
      confirm: '确认',
      delete: '删除',
      cancel: '取消',
      emptyDescription: '暂无 Prompt 数据，请点击右上角新建',
      dialogTitle: '新建 Prompt',
      dialogAlert: '当前还没有可用分类，请先在“分类管理”中新增分类。',
      form: {
        title: '标题',
        titlePlaceholder: '请输入 Prompt 标题',
        author: '作者',
        authorPlaceholder: '请输入作者（可选）',
        description: '描述',
        descriptionPlaceholder: '简要说明该 Prompt 的用途',
        class: '所属分类',
        classPlaceholder: '请选择分类',
        tags: '标签',
        tagsPlaceholder: '请选择标签',
        version: '版本号',
        versionPlaceholder: '如 v1.0.0',
        content: '内容',
        contentPlaceholder: '请输入 Prompt 文本内容'
      },
      footer: {
        cancel: '取消',
        submit: '提交'
      },
      messages: {
        missingRequired: '请至少填写标题、版本号和内容',
        selectClass: '请先选择分类',
        createSuccess: '新建 Prompt 成功',
        createFailed: '新建 Prompt 失败',
        deleteSuccess: '已删除「{name}」',
        deleteFailed: '删除 Prompt 失败',
        resourceNotFound: '相关资源不存在',
        loadPromptFailed: '加载 Prompt 列表失败',
        loadCollectionFailed: '加载分类或标签数据失败'
      }
    },
    promptClassManagement: {
      headerTitle: '分类管理',
      headerDescription: '集中维护 Prompt 分类结构，查看各分类下的提示词数量与更新时间。',
      newClass: '新建分类',
      summary: '共 {totalClasses} 个分类 · 覆盖 {totalPrompts} 条 Prompt',
      empty: '暂无分类数据',
      columns: {
        name: '分类名称',
        description: '分类描述',
        promptCount: 'Prompt 数量',
        createdAt: '创建时间',
        latestUpdated: '最近更新',
        actions: '操作'
      },
      delete: '删除',
      dialogTitle: '新建分类',
      form: {
        name: '分类名称',
        namePlaceholder: '请输入分类名称',
        description: '分类描述',
        descriptionPlaceholder: '请输入分类描述（可选）'
      },
      footer: {
        cancel: '取消',
        submit: '提交'
      },
      messages: {
        loadFailed: '加载分类数据失败，请稍后重试',
        nameRequired: '请填写分类名称',
        createSuccess: '分类创建成功',
        createFailed: '创建分类失败，请稍后重试',
        deleteConfirmTitle: '删除确认',
        deleteConfirmMessage: '确认删除分类“{name}”及其关联关系？',
        confirmDelete: '确认删除',
        deleteSuccess: '分类已删除',
        deleteFailed: '删除分类失败，请稍后重试',
        deleteBlocked: '仍有关联 Prompt 使用该分类，请先迁移或删除后再尝试'
      }
    },
    promptTagManagement: {
      headerTitle: '标签管理',
      headerDescription: '维护标签名称与颜色，掌握标签在 Prompt 中的使用频次。',
      newTag: '新建标签',
      summary: '共 {totalTags} 个标签 · 覆盖 {totalPrompts} 条 Prompt',
      empty: '暂无标签数据',
      columns: {
        tag: '标签',
        color: '颜色',
        promptCount: '引用 Prompt 数',
        createdAt: '创建时间',
        updatedAt: '最近更新',
        actions: '操作'
      },
      delete: '删除',
      dialogTitle: '新建标签',
      form: {
        name: '标签名称',
        namePlaceholder: '请输入标签名称',
        color: '标签颜色'
      },
      footer: {
        cancel: '取消',
        submit: '提交'
      },
      messages: {
        loadFailed: '加载标签数据失败，请稍后重试',
        nameRequired: '请填写标签名称',
        createSuccess: '标签创建成功',
        createFailed: '创建标签失败，请稍后重试',
        deleteConfirmTitle: '删除确认',
        deleteConfirmMessage: '确认删除标签“{name}”并解除关联？',
        confirmDelete: '确认删除',
        deleteSuccess: '标签已删除',
        deleteFailed: '删除标签失败，请稍后重试',
        deleteBlocked: '仍有关联 Prompt 使用该标签，请先迁移或删除后再尝试'
      }
    },
    quickTest: {
      headerTitle: '快速测试',
      headerDescription: '针对单个 Prompt 快速发起临时调用，验证模型输出效果。',
      historyPlaceholder: '历史记录',
      newChat: '新建对话',
      sections: {
        model: '模型与参数',
        chat: '对话调试'
      },
      form: {
        modelLabel: '模型选择',
        modelPlaceholder: '先选择厂商，再选择模型',
        temperatureLabel: '温度',
        extraParamsLabel: '额外参数',
        extraParamsPlaceholder: '请输入 JSON 格式的模型附加参数'
      },
      chat: {
        empty: '发送首条消息以查看模型响应',
        inputPlaceholder: '在此输入测试内容，支持多行输入',
        promptPlaceholder: '选择历史 Prompt 与版本',
        save: '保存为 Prompt',
        send: '发送',
        tokens: {
          input: '输入 Token',
          output: '输出 Token',
          total: '总计'
        },
        avatar: {
          user: '用户',
          self: '我',
          assistant: '助手',
          system: '系统'
        }
      },
      dialog: {
        title: '保存为 Prompt',
        modeLabel: '保存方式',
        modes: {
          new: '新建 Prompt',
          existing: '追加版本'
        },
        classLabel: '分类',
        classPlaceholder: '选择已有分类',
        nameLabel: '名称',
        namePlaceholder: '请输入 Prompt 名称',
        tagsLabel: '标签',
        tagsPlaceholder: '可选择一个或多个标签',
        versionLabel: '版本标签',
        versionPlaceholderNew: '例如 v1',
        versionPlaceholderExisting: '例如 v2',
        descriptionLabel: '描述',
        descriptionPlaceholder: '可选：补充说明',
        promptLabel: '选择 Prompt',
        promptPlaceholder: '请选择 Prompt',
        contentLabel: '内容',
        actions: {
          cancel: '取消',
          save: '保存'
        }
      },
      session: {
        optionLabel: '{prefix}{title}（{timestamp}）',
        draftPrefix: '草稿·',
        newTitle: '新的对话 {id}',
        historyTitle: '历史对话 {id}'
      },
      messages: {
        draftNotUsed: '当前新建对话尚未使用，请先发送消息',
        extraInvalid: '请输入合法的 JSON 文本',
        extraObjectRequired: '额外参数需为对象结构',
        extraParseFailed: 'JSON 格式解析失败',
        historyLoadFailed: '加载历史记录失败，请稍后再试',
        modelsLoadFailed: '加载模型列表失败，请稍后再试',
        promptsLoadFailed: '加载 Prompt 列表失败，请稍后再试',
        tagsLoadFailed: '加载标签列表失败',
        modelRequired: '请先选择要调用的模型',
        extraFixRequired: '额外参数格式有误，请修正后再发送',
        inputRequired: '请输入要测试的内容',
        requestCancelled: '本次请求已取消',
        invokeFailed: '调用模型失败，请稍后再试',
        saveNoContent: '请输入内容后再保存为 Prompt',
        contentRequired: '内容不能为空',
        nameRequired: '请输入 Prompt 名称',
        createPromptSuccess: '新 Prompt 创建成功',
        selectPromptToUpdate: '请选择要更新的 Prompt',
        versionRequired: '请输入版本标签',
        createPromptVersionSuccess: '已创建新的 Prompt 版本',
        savePromptFailed: '保存 Prompt 失败'
      }
    }
  },
  'en-US': {
    common: {
      notSet: 'Not set',
      cancel: 'Cancel',
      confirm: 'Confirm',
      delete: 'Delete',
      submit: 'Submit',
      save: 'Save',
      create: 'Create',
      edit: 'Edit',
      descriptionNone: 'No description',
      notEnabled: 'Not enabled'
    },
    app: {
      title: 'PromptWorks Console',
      settings: 'Settings',
      languageCn: 'Chinese',
      languageEn: 'English',
      themeDark: 'Dark Mode'
    },
    menu: {
      prompt: 'Prompt Management',
      quickTest: 'Quick Test',
      testJob: 'Test Jobs',
      class: 'Class Management',
      tag: 'Tag Management',
      llm: 'LLM Management',
      usage: 'Usage Management'
    },
    promptManagement: {
      headerTitle: 'Prompt Management',
      headerDescription: 'Manage prompt assets centrally and quickly filter by class, tag, and author.',
      createPrompt: 'New Prompt',
      allClasses: 'All Classes',
      searchPlaceholder: 'Search title / content / author',
      tagPlaceholder: 'Filter by tags',
      sortPlaceholder: 'Sort By',
      sortDefault: 'Default Order',
      sortCreatedAt: 'By Creation Time',
      sortUpdatedAt: 'By Update Time',
      sortAuthor: 'By Author',
      currentVersion: 'Current Version',
      author: 'Author',
      createdAt: 'Created At',
      updatedAt: 'Updated At',
      confirmDelete: 'Delete “{name}”?',
      confirm: 'Confirm',
      delete: 'Delete',
      cancel: 'Cancel',
      emptyDescription: 'No prompt data yet. Click “New Prompt” to create.',
      dialogTitle: 'New Prompt',
      dialogAlert: 'No class available. Please create one under “Class Management”.',
      form: {
        title: 'Title',
        titlePlaceholder: 'Enter prompt title',
        author: 'Author',
        authorPlaceholder: 'Enter author (optional)',
        description: 'Description',
        descriptionPlaceholder: 'Describe the purpose of this prompt',
        class: 'Class',
        classPlaceholder: 'Select a class',
        tags: 'Tags',
        tagsPlaceholder: 'Select tags',
        version: 'Version',
        versionPlaceholder: 'e.g. v1.0.0',
        content: 'Content',
        contentPlaceholder: 'Enter prompt content'
      },
      footer: {
        cancel: 'Cancel',
        submit: 'Submit'
      },
      messages: {
        missingRequired: 'Please fill in title, version, and content.',
        selectClass: 'Please select a class first.',
        createSuccess: 'Prompt created successfully.',
        createFailed: 'Failed to create prompt.',
        deleteSuccess: 'Prompt “{name}” has been deleted.',
        deleteFailed: 'Failed to delete prompt.',
        resourceNotFound: 'Resource not found.',
        loadPromptFailed: 'Failed to load prompt list.',
        loadCollectionFailed: 'Failed to load classes or tags.'
      }
    },
    promptClassManagement: {
      headerTitle: 'Class Management',
      headerDescription: 'Maintain prompt class structures and track prompt counts and updates.',
      newClass: 'New Class',
      summary: '{totalClasses} classes · covering {totalPrompts} prompts',
      empty: 'No class data yet',
      columns: {
        name: 'Class Name',
        description: 'Description',
        promptCount: 'Prompt Count',
        createdAt: 'Created At',
        latestUpdated: 'Last Updated',
        actions: 'Actions'
      },
      delete: 'Delete',
      dialogTitle: 'New Class',
      form: {
        name: 'Class Name',
        namePlaceholder: 'Enter class name',
        description: 'Description',
        descriptionPlaceholder: 'Enter description (optional)'
      },
      footer: {
        cancel: 'Cancel',
        submit: 'Submit'
      },
      messages: {
        loadFailed: 'Failed to load class data. Please try again later.',
        nameRequired: 'Please provide a class name.',
        createSuccess: 'Class created successfully.',
        createFailed: 'Failed to create class. Please try again later.',
        deleteConfirmTitle: 'Delete Confirmation',
        deleteConfirmMessage: 'Delete class “{name}” and its relationships?',
        confirmDelete: 'Delete',
        deleteSuccess: 'Class deleted.',
        deleteFailed: 'Failed to delete class. Please try again later.',
        deleteBlocked: 'Some prompts still use this class. Please migrate or remove them first.'
      }
    },
    promptTagManagement: {
      headerTitle: 'Tag Management',
      headerDescription: 'Manage tag labels and colors, and track their usage across prompts.',
      newTag: 'New Tag',
      summary: '{totalTags} tags · covering {totalPrompts} prompts',
      empty: 'No tag data yet',
      columns: {
        tag: 'Tag',
        color: 'Color',
        promptCount: 'Prompt Count',
        createdAt: 'Created At',
        updatedAt: 'Updated At',
        actions: 'Actions'
      },
      delete: 'Delete',
      dialogTitle: 'New Tag',
      form: {
        name: 'Tag Name',
        namePlaceholder: 'Enter tag name',
        color: 'Tag Color'
      },
      footer: {
        cancel: 'Cancel',
        submit: 'Submit'
      },
      messages: {
        loadFailed: 'Failed to load tag data. Please try again later.',
        nameRequired: 'Please provide a tag name.',
        createSuccess: 'Tag created successfully.',
        createFailed: 'Failed to create tag. Please try again later.',
        deleteConfirmTitle: 'Delete Confirmation',
        deleteConfirmMessage: 'Delete tag “{name}” and detach from prompts?',
        confirmDelete: 'Delete',
        deleteSuccess: 'Tag deleted.',
        deleteFailed: 'Failed to delete tag. Please try again later.',
        deleteBlocked: 'Some prompts still use this tag. Please migrate or remove them first.'
      }
    },
    quickTest: {
      headerTitle: 'Quick Test',
      headerDescription: 'Launch ad-hoc calls for a single prompt to validate model outputs.',
      historyPlaceholder: 'History',
      newChat: 'New Conversation',
      sections: {
        model: 'Model & Parameters',
        chat: 'Conversation Debugging'
      },
      form: {
        modelLabel: 'Model Selection',
        modelPlaceholder: 'Pick a provider first, then choose a model',
        temperatureLabel: 'Temperature',
        extraParamsLabel: 'Extra Parameters',
        extraParamsPlaceholder: 'Enter additional parameters in JSON format'
      },
      chat: {
        empty: 'Send the first message to receive a response',
        inputPlaceholder: 'Type test content here. Multi-line is supported.',
        promptPlaceholder: 'Select prompt history and version',
        save: 'Save as Prompt',
        send: 'Send',
        tokens: {
          input: 'Input Tokens',
          output: 'Output Tokens',
          total: 'Total'
        },
        avatar: {
          user: 'User',
          self: 'Me',
          assistant: 'Assistant',
          system: 'System'
        }
      },
      dialog: {
        title: 'Save as Prompt',
        modeLabel: 'Save Mode',
        modes: {
          new: 'Create Prompt',
          existing: 'Append Version'
        },
        classLabel: 'Class',
        classPlaceholder: 'Select an existing class',
        nameLabel: 'Name',
        namePlaceholder: 'Enter prompt name',
        tagsLabel: 'Tags',
        tagsPlaceholder: 'Select one or more tags',
        versionLabel: 'Version Tag',
        versionPlaceholderNew: 'e.g. v1',
        versionPlaceholderExisting: 'e.g. v2',
        descriptionLabel: 'Description',
        descriptionPlaceholder: 'Optional: add extra notes',
        promptLabel: 'Prompt',
        promptPlaceholder: 'Select a prompt',
        contentLabel: 'Content',
        actions: {
          cancel: 'Cancel',
          save: 'Save'
        }
      },
      session: {
        optionLabel: '{prefix}{title} ({timestamp})',
        draftPrefix: 'Draft · ',
        newTitle: 'New conversation {id}',
        historyTitle: 'History conversation {id}'
      },
      messages: {
        draftNotUsed: 'This draft conversation has no activity yet. Send a message first.',
        extraInvalid: 'Enter a valid JSON string.',
        extraObjectRequired: 'Extra parameters must be an object.',
        extraParseFailed: 'Invalid JSON format.',
        historyLoadFailed: 'Failed to load conversation history. Try again later.',
        modelsLoadFailed: 'Failed to load model list. Try again later.',
        promptsLoadFailed: 'Failed to load prompts. Try again later.',
        tagsLoadFailed: 'Failed to load tags.',
        modelRequired: 'Select a model before sending.',
        extraFixRequired: 'Fix extra parameters before sending.',
        inputRequired: 'Enter content to test.',
        requestCancelled: 'Request cancelled.',
        invokeFailed: 'Model invocation failed. Try again later.',
        saveNoContent: 'Enter content before saving as a prompt.',
        contentRequired: 'Content cannot be empty.',
        nameRequired: 'Enter a prompt name.',
        createPromptSuccess: 'Prompt created successfully.',
        selectPromptToUpdate: 'Select a prompt to update.',
        versionRequired: 'Enter a version tag.',
        createPromptVersionSuccess: 'New prompt version created.',
        savePromptFailed: 'Failed to save prompt.'
      }
    }
  }
} as const

export type SupportedLocale = keyof typeof messages
