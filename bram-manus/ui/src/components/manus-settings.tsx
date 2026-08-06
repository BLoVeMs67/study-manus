"use client"


import {Dialog, DialogTrigger} from "@/components/ui/dialog";
import {Button} from "@/components/ui/button";

export function ManusSettings() {
  return (
      <Dialog open={open} onOpenChange={setOpen}>
        {/* 触发按钮 */}
        <DialogTrigger asChild>
          <Button variant="outline" size="icon-sm" className="cursor-pointer">
            <Settings/>
          </Button>
        </DialogTrigger>

        {/* 弹窗内容 */}
        <DialogContent className="!max-w-[850px]">
          {/* 头部 */}
          <DialogHeader className="border-b pb-4">
            <DialogTitle className="text-gray-700">MoocManus 设置</DialogTitle>
            <DialogDescription className="text-gray-500">在此管理您的 MoocManus 设置。</DialogDescription>
          </DialogHeader>

          {/* 中间主体 */}
          <div className="flex flex-row gap-4">
            {/* 左侧导航菜单 */}
            <div className="max-w-[180px]">
              <div className="flex flex-col gap-0">
                {SETTING_MENUS.map((menu) => (
                    <Button
                        key={menu.key}
                        variant={activeSetting === menu.key ? 'default' : 'ghost'}
                        className="cursor-pointer justify-start"
                        onClick={() => setActiveSetting(menu.key)}
                    >
                      <menu.icon/>
                      {menu.title}
                    </Button>
                ))}
              </div>
            </div>

            {/* 分隔符 */}
            <Separator orientation="vertical"/>

            {/* 右侧内容 */}
            <div className="flex-1 h-[500px] scrollbar-hide overflow-y-auto">
              {loadingConfig && (activeSetting === 'common-setting' || activeSetting === 'llm-setting') ? (
                  <div className="flex justify-center items-center h-full">
                    <Loader2 className="size-6 animate-spin text-muted-foreground"/>
                  </div>
              ) : (
                  <>
                    {activeSetting === 'common-setting' && (
                        <CommonSetting config={agentConfig} onChange={setAgentConfig}/>
                    )}
                    {activeSetting === 'llm-setting' && (
                        <LLMSetting config={llmConfig} onChange={setLlmConfig}/>
                    )}
                  </>
              )}
              {activeSetting === 'a2a-setting' && (
                  <A2ASetting
                      servers={a2aServers}
                      loading={loadingA2A}
                      onToggleEnabled={handleA2AToggle}
                      onDelete={handleA2ADelete}
                      onAdd={handleA2AAdd}
                  />
              )}
              {activeSetting === 'mcp-setting' && (
                  <MCPSetting
                      servers={mcpServers}
                      loading={loadingMCP}
                      onToggleEnabled={handleMCPToggle}
                      onDelete={handleMCPDelete}
                      onAdd={handleMCPAdd}
                  />
              )}
            </div>
          </div>

          {/* 底部按钮 */}
          <DialogFooter className="border-t pt-4">
            <DialogClose asChild>
              <Button variant="outline" className="cursor-pointer">取消</Button>
            </DialogClose>
            <Button
                className="cursor-pointer"
                disabled={saving}
                onClick={handleSave}
            >
              {saving && <Loader2 className="animate-spin"/>}
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
  )
}