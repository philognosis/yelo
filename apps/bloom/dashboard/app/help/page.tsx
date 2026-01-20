'use client';

import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import PageHeader from '@/components/PageHeader';
import Card from '@/components/Card';
import Input from '@/components/Input';
import Button from '@/components/Button';

interface FAQItem {
  question: string;
  answer: string;
  category: string;
  roles?: string[];
}

const faqData: FAQItem[] = [
  {
    category: 'General',
    question: 'What is Bloom?',
    answer: 'Bloom is an AI-powered performance evaluation system that streamlines the review process for employees, managers, HR, and committees. It uses advanced AI to provide insights and assist managers in creating comprehensive, fair evaluations.',
  },
  {
    category: 'General',
    question: 'How does the evaluation cycle work?',
    answer: 'An evaluation cycle typically follows these phases: 1) Peer Selection - employees choose peer reviewers, 2) Self-Evaluation - employees assess their own performance, 3) Peer Feedback - peers provide input, 4) Manager Review - managers complete evaluations (with optional AI assistance), 5) Committee Calibration - committee reviews for consistency, 6) Finalization - feedback is shared with employees.',
  },
  {
    category: 'Employee',
    question: 'How do I select peer reviewers?',
    answer: 'Navigate to your evaluation and click on "Select Peers". Choose 3-5 colleagues who have worked closely with you and can provide meaningful feedback. Your manager will review and may adjust your selections.',
    roles: ['employee'],
  },
  {
    category: 'Employee',
    question: 'What should I include in my self-evaluation?',
    answer: 'Be honest and specific. Provide concrete examples of your achievements, challenges you overcame, skills you developed, and areas where you want to grow. Use the STAR method (Situation, Task, Action, Result) to structure your examples.',
    roles: ['employee'],
  },
  {
    category: 'Manager',
    question: 'How does the AI draft feature work?',
    answer: 'The AI analyzes all available data (self-evaluations, peer feedback, performance metrics) and generates a draft evaluation. This includes suggested ratings, evidence-based comments, and clarifying questions to help you provide comprehensive feedback. You can use the draft as-is, modify it, or start from scratch.',
    roles: ['manager'],
  },
  {
    category: 'Manager',
    question: 'Can I edit an evaluation after submitting?',
    answer: 'Once submitted, evaluations enter the committee review phase. If the committee requests changes, you\'ll be able to make revisions. Otherwise, the evaluation becomes final after committee approval.',
    roles: ['manager'],
  },
  {
    category: 'Manager',
    question: 'How should I use the clarifying questions from AI?',
    answer: 'Clarifying questions highlight areas where the AI identified gaps or inconsistencies in the available data. Address these questions to strengthen your evaluation and ensure you\'re providing comprehensive feedback.',
    roles: ['manager'],
  },
  {
    category: 'HR',
    question: 'How do I create a new evaluation cycle?',
    answer: 'Go to HR Dashboard → Cycles → Create New Cycle. Set the cycle name, dates, phase deadlines, select an evaluation template, and choose participant groups. Ensure deadlines allow sufficient time for each phase.',
    roles: ['hr_admin'],
  },
  {
    category: 'HR',
    question: 'How can I track evaluation progress?',
    answer: 'Use the HR Dashboard to view completion rates, pending evaluations, and system-wide metrics. The Analytics page provides detailed insights into rating distributions, department performance, and trends.',
    roles: ['hr_admin'],
  },
  {
    category: 'Committee',
    question: 'What is calibration?',
    answer: 'Calibration ensures consistency and fairness in ratings across teams and departments. The committee reviews manager evaluations, compares them to peer groups and department averages, and adjusts ratings when necessary to maintain organizational standards.',
    roles: ['committee'],
  },
  {
    category: 'Committee',
    question: 'When should I request a manager to revise an evaluation?',
    answer: 'Request revisions when: 1) The rating is significantly different from peer/department averages without clear justification, 2) The evaluation lacks specific evidence or examples, 3) The feedback is not actionable or constructive, 4) There are inconsistencies between competency ratings and the overall rating.',
    roles: ['committee'],
  },
];

export default function HelpPage() {
  const { user } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const categories = Array.from(new Set(faqData.map(faq => faq.category)));

  const filteredFAQs = faqData.filter(faq => {
    const matchesSearch =
      faq.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory =
      selectedCategory === 'all' || faq.category === selectedCategory;

    const matchesRole =
      !faq.roles || faq.roles.includes(user?.role || '');

    return matchesSearch && matchesCategory && matchesRole;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Help & Documentation"
        description="Find answers and learn how to use Bloom effectively"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Help', href: '/help' },
        ]}
      />

      {/* Search and Filter */}
      <Card className="p-6">
        <div className="grid md:grid-cols-2 gap-4">
          <Input
            label="Search"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search for help topics..."
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <div className="flex gap-2 flex-wrap">
              <Button
                variant={selectedCategory === 'all' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setSelectedCategory('all')}
              >
                All
              </Button>
              {categories.map(category => (
                <Button
                  key={category}
                  variant={selectedCategory === category ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={() => setSelectedCategory(category)}
                >
                  {category}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Quick Links */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Quick Links</h2>
        <div className="grid md:grid-cols-3 gap-4">
          <a
            href="#getting-started"
            className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all"
          >
            <div className="text-2xl mb-2">🚀</div>
            <div className="font-medium">Getting Started</div>
            <div className="text-sm text-gray-600 mt-1">New to Bloom?</div>
          </a>

          <a
            href="#video-tutorials"
            className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all"
          >
            <div className="text-2xl mb-2">🎥</div>
            <div className="font-medium">Video Tutorials</div>
            <div className="text-sm text-gray-600 mt-1">Watch how-to guides</div>
          </a>

          <a
            href="#contact-support"
            className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all"
          >
            <div className="text-2xl mb-2">💬</div>
            <div className="font-medium">Contact Support</div>
            <div className="text-sm text-gray-600 mt-1">Get personalized help</div>
          </a>
        </div>
      </Card>

      {/* FAQs */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">Frequently Asked Questions</h2>
        <div className="space-y-4">
          {filteredFAQs.map((faq, index) => (
            <details
              key={index}
              className="group p-4 bg-gray-50 rounded-lg border border-gray-200"
            >
              <summary className="font-semibold cursor-pointer list-none flex items-center justify-between">
                <span className="flex-1">{faq.question}</span>
                <span className="ml-4 text-gray-500 group-open:rotate-180 transition-transform">
                  ▼
                </span>
              </summary>
              <div className="mt-4 text-gray-700 leading-relaxed">
                {faq.answer}
              </div>
            </details>
          ))}
        </div>

        {filteredFAQs.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No results found. Try a different search term or category.
          </div>
        )}
      </Card>

      {/* Role-Specific Guides */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">User Guides</h2>
          <div className="space-y-3">
            <a href="#" className="block p-3 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-all">
              <div className="font-medium text-blue-900">Employee Guide</div>
              <div className="text-sm text-blue-700">Complete your evaluations</div>
            </a>
            <a href="#" className="block p-3 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-all">
              <div className="font-medium text-purple-900">Manager Guide</div>
              <div className="text-sm text-purple-700">Conduct effective reviews</div>
            </a>
            <a href="#" className="block p-3 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition-all">
              <div className="font-medium text-green-900">HR Admin Guide</div>
              <div className="text-sm text-green-700">Manage cycles and settings</div>
            </a>
            <a href="#" className="block p-3 bg-orange-50 border border-orange-200 rounded-lg hover:bg-orange-100 transition-all">
              <div className="font-medium text-orange-900">Committee Guide</div>
              <div className="text-sm text-orange-700">Calibrate evaluations</div>
            </a>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Resources</h2>
          <div className="space-y-3">
            <a href="#" className="block p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-all">
              <div className="font-medium">Writing Effective Feedback</div>
              <div className="text-sm text-gray-600">Best practices and examples</div>
            </a>
            <a href="#" className="block p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-all">
              <div className="font-medium">Understanding AI Drafts</div>
              <div className="text-sm text-gray-600">How AI assists managers</div>
            </a>
            <a href="#" className="block p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-all">
              <div className="font-medium">Rating Guidelines</div>
              <div className="text-sm text-gray-600">Calibration standards</div>
            </a>
            <a href="#" className="block p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-all">
              <div className="font-medium">System Changelog</div>
              <div className="text-sm text-gray-600">Latest updates and features</div>
            </a>
          </div>
        </Card>
      </div>

      {/* Contact Support */}
      <Card className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
        <h2 className="text-xl font-semibold mb-4">Still Need Help?</h2>
        <p className="text-gray-700 mb-4">
          Our support team is here to assist you with any questions or issues.
        </p>
        <div className="flex gap-4">
          <Button variant="primary">
            Contact Support
          </Button>
          <Button variant="ghost">
            Report an Issue
          </Button>
        </div>
      </Card>
    </div>
  );
}
