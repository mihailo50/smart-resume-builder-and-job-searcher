'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { PageTransition } from '@/components/ui/page-transition';
import { Navbar } from '@/components/layout/navbar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  FileText,
  TrendingUp,
  Eye,
  Download,
  Plus,
  Star,
  Calendar,
  Loader2,
  Trash2,
  Edit,
  MoreVertical,
} from 'lucide-react';
import Link from 'next/link';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

interface Resume {
  id: string;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [resumeToDelete, setResumeToDelete] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  interface DashboardStats {
    total_resumes: number;
    average_ats_score: number;
    total_views: number;
    saved_jobs: number;
  }

  interface AnalyticsData {
    month: string;
    score: number;
  }

  // Fetch dashboard stats
  const { data: stats = { total_resumes: 0, average_ats_score: 0, total_views: 0, saved_jobs: 0 }, isLoading: statsLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboardStats'],
    queryFn: async () => {
      try {
        const response = await api.get<DashboardStats>('/v1/dashboard/stats/');
        return response;
      } catch (error: any) {
        console.error('Failed to load dashboard stats:', error);
        // Redirect to login if unauthorized
        if (error?.message?.includes('401') || error?.message?.includes('403')) {
          router.push('/login');
        }
        throw error;
      }
    },
  });

  // Fetch dashboard analytics
  const { data: analyticsResponse, isLoading: analyticsLoading } = useQuery<{ data: AnalyticsData[] }>({
    queryKey: ['dashboardAnalytics'],
    queryFn: async () => {
      try {
        const response = await api.get<{ data: AnalyticsData[] }>('/v1/dashboard/analytics/');
        return response;
      } catch (error: any) {
        console.error('Failed to load dashboard analytics:', error);
        // Redirect to login if unauthorized
        if (error?.message?.includes('401') || error?.message?.includes('403')) {
          router.push('/login');
        }
        throw error;
      }
    },
  });

  // Fetch resumes
  const { data: resumes = [], isLoading, refetch } = useQuery<Resume[]>({
    queryKey: ['userResumes'],
    queryFn: async () => {
      try {
        const response = await api.get<Resume[]>('/v1/resumes/');
        return response;
      } catch (error: any) {
        console.error('Failed to load resumes:', error);
        toast.error('Failed to load resumes');
        // Redirect to login if unauthorized
        if (error?.message?.includes('401') || error?.message?.includes('403')) {
          router.push('/login');
        }
        throw error;
      }
    },
  });

  const handleExport = async (resumeId: string) => {
    try {
      router.push(`/builder/preview?id=${resumeId}`);
    } catch (error) {
      toast.error('Failed to open resume');
    }
  };

  const handleDelete = async (resumeId: string) => {
    try {
      setDeleting(true);
      await api.delete(`/v1/resumes/${resumeId}/`);
      toast.success('Resume deleted successfully');
      setDeleteDialogOpen(false);
      setResumeToDelete(null);
      // Reload resumes
      refetch();
    } catch (error: any) {
      console.error('Failed to delete resume:', error);
      toast.error(error?.message || 'Failed to delete resume');
    } finally {
      setDeleting(false);
    }
  };

  const handleEdit = (resumeId: string) => {
    router.push(`/builder/personal?id=${resumeId}`);
  };

  // Use analytics data from backend or fallback to empty array
  const analyticsData: AnalyticsData[] = analyticsResponse?.data || [];

  return (
    <PageTransition>
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
        <Navbar />
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
          <div className="max-w-7xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-8"
            >
              <h1 className="text-4xl md:text-5xl font-bold mb-4">Dashboard</h1>
              <p className="text-xl text-muted-foreground">
                Manage your resumes and track your progress
              </p>
            </motion.div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Total Resumes
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{statsLoading ? '...' : stats.total_resumes}</div>
                  </CardContent>
                </Card>
              </motion.div>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Average ATS Score
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{statsLoading ? '...' : Math.round(stats.average_ats_score)}</div>
                  </CardContent>
                </Card>
              </motion.div>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Total Views
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{statsLoading ? '...' : stats.total_views}</div>
                  </CardContent>
                </Card>
              </motion.div>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
              >
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Saved Jobs
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{statsLoading ? '...' : stats.saved_jobs}</div>
                  </CardContent>
                </Card>
              </motion.div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* Recent Resumes */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle>Recent Resumes</CardTitle>
                      <Button asChild variant="outline" size="sm">
                        <Link href="/builder">
                          <Plus className="mr-2 h-4 w-4" />
                          New Resume
                        </Link>
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {isLoading ? (
                      <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        <span className="ml-3 text-muted-foreground">Loading resumes...</span>
                      </div>
                    ) : resumes.length === 0 ? (
                      <div className="text-center py-12">
                        <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                        <p className="text-muted-foreground mb-4">No resumes yet</p>
                        <Button asChild>
                          <Link href="/builder/personal">
                            <Plus className="mr-2 h-4 w-4" />
                            Create Your First Resume
                          </Link>
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {(resumes || []).slice(0, 5).map((resume, index) => (
                          <motion.div
                            key={resume.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                            whileHover={{ scale: 1.02 }}
                          >
                            <Card className="border-2 hover:border-primary transition-colors cursor-pointer" onClick={() => router.push(`/builder/preview?id=${resume.id}`)}>
                              <CardContent className="p-4">
                                <div className="flex items-center justify-between mb-3">
                                  <div className="flex items-center gap-2">
                                    <FileText className="h-5 w-5 text-primary" />
                                    <span className="font-semibold">{resume.title}</span>
                                  </div>
                                  <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20">
                                    {resume.status}
                                  </Badge>
                                </div>
                                <div className="flex items-center justify-between text-sm text-muted-foreground">
                                  <div className="flex items-center gap-4">
                                    <span className="flex items-center gap-1">
                                      <Calendar className="h-4 w-4" />
                                      {formatDistanceToNow(new Date(resume.updated_at), { addSuffix: true })}
                                    </span>
                                  </div>
                                  <DropdownMenu>
                                    <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                                      <Button variant="ghost" size="sm">
                                        <MoreVertical className="h-4 w-4" />
                                      </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end">
                                      <DropdownMenuLabel>Actions</DropdownMenuLabel>
                                      <DropdownMenuSeparator />
                                      <DropdownMenuItem onClick={() => handleEdit(resume.id)}>
                                        <Edit className="mr-2 h-4 w-4" />
                                        Edit
                                      </DropdownMenuItem>
                                      <DropdownMenuItem onClick={() => handleExport(resume.id)}>
                                        <Download className="mr-2 h-4 w-4" />
                                        Export
                                      </DropdownMenuItem>
                                      <DropdownMenuItem
                                        onClick={() => router.push(`/builder/preview?id=${resume.id}`)}
                                      >
                                        <Eye className="mr-2 h-4 w-4" />
                                        Preview
                                      </DropdownMenuItem>
                                      <DropdownMenuSeparator />
                                      <DropdownMenuItem
                                        className="text-destructive"
                                        onClick={() => {
                                          setResumeToDelete(resume.id);
                                          setDeleteDialogOpen(true);
                                        }}
                                      >
                                        <Trash2 className="mr-2 h-4 w-4" />
                                        Delete
                                      </DropdownMenuItem>
                                    </DropdownMenuContent>
                                  </DropdownMenu>
                                </div>
                              </CardContent>
                            </Card>
                          </motion.div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>

              {/* Analytics Chart */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-primary" />
                      ATS Score Over Time
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {analyticsLoading ? (
                      <div className="flex items-center justify-center h-[300px]">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                      </div>
                    ) : analyticsData.length === 0 ? (
                      <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                        No analytics data available yet
                      </div>
                    ) : (
                      <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={analyticsData}>
                        <defs>
                          <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis dataKey="month" className="text-xs" />
                        <YAxis className="text-xs" />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'hsl(var(--card))',
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '0.5rem',
                          }}
                        />
                        <Area
                          type="monotone"
                          dataKey="score"
                          stroke="#6366f1"
                          fillOpacity={1}
                          fill="url(#colorScore)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            </div>
          </div>
        </div>

        {/* Delete Confirmation Dialog */}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Resume</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete this resume? This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={() => resumeToDelete && handleDelete(resumeToDelete)}
                disabled={deleting}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                {deleting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  'Delete'
                )}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </PageTransition>
  );
}


