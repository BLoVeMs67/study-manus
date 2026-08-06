// 定义页面路由参数
interface PageProps {
  params: Promise<{ id: string }>
}

export default async function Page(
    {params}: PageProps,
) {
  const {id} = await params
  return (
      <div>会话列表页: {id}</div>
  )
}