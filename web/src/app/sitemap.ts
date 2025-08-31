import { MetadataRoute } from 'next'
import { promises as fs } from 'fs'
import path from 'path'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = 'https://outils-citoyens.vercel.app'
  
  // Static pages
  const staticPages = [
    {
      url: baseUrl,
      lastModified: new Date(),
      changeFrequency: 'weekly' as const,
      priority: 1,
    },
    {
      url: `${baseUrl}/assistant`,
      lastModified: new Date(),
      changeFrequency: 'weekly' as const,
      priority: 0.9,
    },
  ]

  // Dynamic tool pages - read from public/schemas directory
  const schemasDir = path.join(process.cwd(), 'public', 'schemas')
  let toolPages: MetadataRoute.Sitemap = []

  try {
    const files = await fs.readdir(schemasDir)
    const jsonFiles = files.filter(file => file.endsWith('.json'))
    
    toolPages = jsonFiles.map(file => {
      const toolId = file.replace('.json', '')
      return {
        url: `${baseUrl}/outil/${toolId}`,
        lastModified: new Date(),
        changeFrequency: 'weekly' as const,
        priority: 0.8,
      }
    })
  } catch (error) {
    console.error('Error reading schemas directory:', error)
  }

  return [...staticPages, ...toolPages]
}