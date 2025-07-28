// frontend/src/components/emissions/Scope3Form.tsx

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Select, 
  InputNumber, 
  Button, 
  Table, 
  Space,
  Typography,
  Alert,
  Progress,
  Statistic
} from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { SCOPE3_CATEGORIES, getCategoryDisplayName } from '@/constants/scope3Categories';
import { calculateScope3Emissions, getEmissionFactors } from '@/services/scope3Api';

const { Title, Text } = Typography;
const { Option } = Select;

export const Scope3Form: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [availableFactors, setAvailableFactors] = useState<any[]>([]);
  const [activities, setActivities] = useState<any[]>([{
    factor_name: '',
    quantity: 0,
    unit: '',
    calculation_method: 'activity_based'
  }]);
  const [calculating, setCalculating] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    if (selectedCategory) {
      loadFactors();
    }
  }, [selectedCategory]);

  const loadFactors = async () => {
    try {
      const response = await getEmissionFactors(selectedCategory);
      setAvailableFactors(response.factors);
    } catch (error) {
      console.error('Failed to load factors:', error);
    }
  };

  const handleCalculate = async () => {
    setCalculating(true);
    try {
      const response = await calculateScope3Emissions({
        category: selectedCategory,
        activity_data: activities,
        reporting_period: new Date().getFullYear().toString()
      });
      setResult(response);
    } catch (error) {
      console.error('Calculation failed:', error);
    } finally {
      setCalculating(false);
    }
  };

  return (
    <Card>
      <Title level={3}>Calculate Scope 3 Emissions</Title>
      
      <Form layout="vertical">
        <Form.Item label="Category">
          <Select
            value={selectedCategory}
            onChange={setSelectedCategory}
            placeholder="Select a Scope 3 category"
            size="large"
          >
            {Object.entries(SCOPE3_CATEGORIES).map(([key, category]) => (
              <Option key={key} value={key}>
                {category.displayName}
              </Option>
            ))}
          </Select>
        </Form.Item>

        {selectedCategory && (
          <>
            <Alert
              message={SCOPE3_CATEGORIES[selectedCategory as keyof typeof SCOPE3_CATEGORIES].description}
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Title level={4}>Activity Data</Title>
            <Table
              dataSource={activities}
              columns={[
                {
                  title: 'Emission Factor',
                  dataIndex: 'factor_name',
                  render: (_, record, index) => (
                    <Select
                      value={record.factor_name}
                      onChange={(value) => {
                        const factor = availableFactors.find(f => f.name === value);
                        const newActivities = [...activities];
                        newActivities[index] = {
                          ...newActivities[index],
                          factor_name: value,
                          unit: factor?.unit || ''
                        };
                        setActivities(newActivities);
                      }}
                      style={{ width: 300 }}
                    >
                      {availableFactors.map(factor => (
                        <Option key={factor.id} value={factor.name}>
                          {factor.name} ({factor.unit})
                        </Option>
                      ))}
                    </Select>
                  )
                },
                {
                  title: 'Quantity',
                  dataIndex: 'quantity',
                  render: (_, record, index) => (
                    <InputNumber
                      value={record.quantity}
                      onChange={(value) => {
                        const newActivities = [...activities];
                        newActivities[index].quantity = value || 0;
                        setActivities(newActivities);
                      }}
                      min={0}
                      style={{ width: 150 }}
                    />
                  )
                },
                {
                  title: 'Unit',
                  dataIndex: 'unit',
                  render: (text) => <Text>{text}</Text>
                },
                {
                  title: 'Action',
                  render: (_, __, index) => (
                    <Button
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => {
                        setActivities(activities.filter((_, i) => i !== index));
                      }}
                      disabled={activities.length === 1}
                    />
                  )
                }
              ]}
              pagination={false}
            />
            
            <Space style={{ marginTop: 16 }}>
              <Button
                icon={<PlusOutlined />}
                onClick={() => {
                  setActivities([...activities, {
                    factor_name: '',
                    quantity: 0,
                    unit: '',
                    calculation_method: 'activity_based'
                  }]);
                }}
              >
                Add Activity
              </Button>
              
              <Button
                type="primary"
                onClick={handleCalculate}
                loading={calculating}
                disabled={!activities.some(a => a.factor_name && a.quantity > 0)}
              >
                Calculate Emissions
              </Button>
            </Space>
          </>
        )}
      </Form>

      {result && (
        <Card style={{ marginTop: 24 }}>
          <Title level={4}>Results</Title>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Statistic
              title="Total Emissions"
              value={result.emissions_tco2e}
              suffix="tCO2e"
              precision={3}
            />
            
            <Alert
              message={`Uncertainty: ±${result.uncertainty_percent.toFixed(1)}%`}
              description={`95% Confidence Interval: ${result.confidence_interval.lower.toFixed(3)} - ${result.confidence_interval.upper.toFixed(3)} tCO2e`}
              type="warning"
            />
            
            <Progress
              percent={result.data_quality_score}
              status="active"
              format={percent => `Data Quality: ${percent}%`}
            />
            
            {result.esrs_requirements && (
              <Alert
                message="ESRS Requirements"
                description={result.esrs_requirements.join(', ')}
                type="info"
              />
            )}
          </Space>
        </Card>
      )}
    </Card>
  );
};