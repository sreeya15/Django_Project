from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from .models import Demand, STAGE_COLORS, DemandStagePeriod, Stage, STAGE_ORDER
from .forms import DemandForm, DemandStagePeriodForm
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

def demand_list(request):
    demands = Demand.objects.all().prefetch_related('stages')
    
    # If there are no demands, return early with empty context
    if not demands.exists():
        return render(request, 'trackerapp/demand_list.html', {
            'demand_data': [],
            'stage_legend': []
        })
    
    # Find the earliest start date and latest end date across all demands to determine the global timeline
    earliest_start_date = None
    latest_end_date = None
    
    for demand in demands:
        # Check demand start date
        if demand.start_date:
            if earliest_start_date is None or demand.start_date < earliest_start_date:
                earliest_start_date = demand.start_date
            
            # Calculate end date based on duration_months if available
            if demand.duration_months:
                demand_end = demand.get_end_date()
                if demand_end and (latest_end_date is None or demand_end > latest_end_date):
                    latest_end_date = demand_end
        
        # Check all stage dates for this demand
        stages = list(demand.stages.all())
        if stages:
            stage_start_dates = [s.start_date for s in stages]
            stage_end_dates = [s.end_date for s in stages]
            
            min_stage_date = min(stage_start_dates) if stage_start_dates else None
            max_stage_date = max(stage_end_dates) if stage_end_dates else None
            
            if min_stage_date and (earliest_start_date is None or min_stage_date < earliest_start_date):
                earliest_start_date = min_stage_date
            
            if max_stage_date and (latest_end_date is None or max_stage_date > latest_end_date):
                latest_end_date = max_stage_date
    
    # Default values if no dates found
    if earliest_start_date is None:
        earliest_start_date = date(2025, 1, 1)
    if latest_end_date is None:
        # Default to 1 year from earliest start if no end dates found
        latest_end_date = earliest_start_date + relativedelta(years=1)
    
    # Adjust to the start of the year for cleaner display
    global_timeline_start = earliest_start_date.replace(month=1, day=1)
    
    # Add a buffer at the end for better visualization (extend to the end of the year)
    global_timeline_end = latest_end_date.replace(month=12, day=31)
    
    # Use exact timeline based on demand durations without minimum years constraint
    # Just ensure we always show complete years by adjusting to year boundaries
    # No minimum timeline span enforced - shows exactly what's needed by demands
    
    # Calculate the total duration in days for the global timeline
    global_timeline_days = (global_timeline_end - global_timeline_start).days + 1
    
    # === Quarter Markers ===
    quarter_markers = []
    start_year = global_timeline_start.year
    end_year = global_timeline_end.year
    
    for year in range(start_year, end_year + 1):
        for quarter in range(1, 5):
            quarter_month = (quarter - 1) * 3 + 1
            quarter_date = date(year, quarter_month, 1)
            
            if quarter_date < global_timeline_start or quarter_date > global_timeline_end:
                continue
                
            days_from_start = (quarter_date - global_timeline_start).days
            position_percent = (days_from_start / global_timeline_days) * 100
            
            quarter_markers.append({
                'date': quarter_date.strftime('%Y-%m-%d'),
                'label': f"Q{quarter}",
                'position': position_percent
            })

    # === Year Markers ===
    timeline_years = []
    # Timeline spans from start_year to end_year based on actual demand durations
    for year in range(start_year, end_year + 1):
        year_start = date(year, 1, 1)
        if year_start < global_timeline_start:
            year_start = global_timeline_start
            
        days_from_start = (year_start - global_timeline_start).days
        position_percent = (days_from_start / global_timeline_days) * 100
        
        timeline_years.append({
            'label': str(year),
            'position': position_percent,
            'year': year
        })

    # === Month Markers ===
    month_markers = []
    current_date = global_timeline_start
    while current_date <= global_timeline_end:
        days_from_start = (current_date - global_timeline_start).days
        position_percent = (days_from_start / global_timeline_days) * 100
        month_markers.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'label': current_date.strftime('%b'),
            'position': position_percent
        })
        current_date += relativedelta(months=1)
    
    # === Demand and Stage Bars ===
    demand_data = []
    
    # Get current stages from session if available
    demand_current_stages = request.session.get('demand_current_stages', {})
    for demand in demands:
        stages = list(demand.stages.all())
        stage_bars = []
        
        # Determine demand start and end dates
        demand_start = demand.start_date
        demand_end = demand.get_end_date() if demand_start and demand.duration_months else None
        
        # If demand doesn't have dates but has stages, use stage dates
        if (not demand_start or not demand_end) and stages:
            all_dates = [s.start_date for s in stages] + [s.end_date for s in stages]
            if all_dates:  # Check if list is not empty
                demand_start = min(all_dates)
                demand_end = max(all_dates)
        
        # Skip if we still don't have valid dates
        if not demand_start or not demand_end:
            continue
            
        # Calculate demand duration in global timeline
        demand_duration_days = (demand_end - demand_start).days + 1
        demand_start_offset = (demand_start - global_timeline_start).days
        demand_start_percent = max(0, (demand_start_offset / global_timeline_days) * 100)
        demand_width_percent = max(0.5, (demand_duration_days / global_timeline_days) * 100)
        
        for s in stages:
            if not (s.start_date and s.end_date):
                continue
                
            # Calculate stage position relative to the demand's timeline
            stage_duration = (s.end_date - s.start_date).days + 1
            
            # Calculate stage position relative to its demand's timeline (not global timeline)
            stage_start_offset = (s.start_date - demand_start).days
            stage_relative_start = (stage_start_offset / demand_duration_days) * 100
            stage_relative_width = (stage_duration / demand_duration_days) * 100
            
            # Convert relative position within demand to position within the container
            # This ensures the stage bar appears inside the demand timeline
            stage_start_percent = demand_start_percent + (demand_width_percent * stage_relative_start / 100)
            stage_width_percent = demand_width_percent * stage_relative_width / 100
            
            # Calculate positions for fixed timeline 2025-2029 by months for more precision
            # Each year is 20% of timeline (5 years total)
            # Each month is 1.667% of the timeline (12 months per year)
            start_year = s.start_date.year
            start_month = s.start_date.month
            start_day = s.start_date.day
            
            end_year = s.end_date.year
            end_month = s.end_date.month
            end_day = s.end_date.day
            
            # Calculate month-based positions (more precise than quarters)
            # For each year, add 20% to the position
            # For each month, add 1.667% to the position
            year_diff_start = start_year - 2025
            month_position_start = (start_month - 1) * (20/12)  # Each month is 1/12 of a year's 20%
            # Add partial month based on day (optional for more precision)
            day_position_start = (start_day - 1) * (20/12/30)  # Approximate days in month
            
            year_diff_end = end_year - 2025
            month_position_end = (end_month - 1) * (20/12)
            # Add partial month based on day (optional for more precision)
            day_position_end = (end_day - 1) * (20/12/30)  # Approximate days in month
            
            # Final positions as percentages
            start_pos = (year_diff_start * 20) + month_position_start + day_position_start
            end_pos = (year_diff_end * 20) + month_position_end + day_position_end
            
            # Calculate width precisely based on actual start and end positions
            width = end_pos - start_pos
            
            # For quarter display in the template, still keep quarter calculations
            start_quarter = (start_month - 1) // 3
            end_quarter = (end_month - 1) // 3
            
            # Handle stage number and label safely based on stage type
            stage_number = STAGE_ORDER.get(s.stage, 0)
            stage_color = STAGE_COLORS.get(s.stage, '#888')
            should_show_number = True
            
            # Check if this is our custom mini progress stage
            if s.stage == 'mini_progress':
                # Get the current stage for this demand from the session
                demand_id_str = str(demand.id)
                if demand_id_str in demand_current_stages:
                    # Use the current stage color and number
                    current_stage = demand_current_stages[demand_id_str]
                    stage_number = STAGE_ORDER.get(current_stage, 0)
                    stage_color = STAGE_COLORS.get(current_stage, '#444444')
                    stage_verbose = Stage(current_stage).label
                    should_show_number = True
                else:
                    # Default mini progress bar appearance
                    stage_verbose = "Duration"
                    stage_color = '#444444'  # Dark gray
                    should_show_number = False
            else:
                stage_verbose = Stage(s.stage).label
                
            stage_bars.append({
                'id': s.id,
                'stage': s.stage,
                'stage_number': stage_number,
                'stage_verbose': stage_verbose,
                'color': stage_color,
                'start_percent': stage_start_percent,
                'width_percent': stage_width_percent,
                'relative_start_percent': stage_relative_start,
                'relative_width_percent': stage_relative_width,
                'duration': stage_duration,
                'start_date': s.start_date.strftime('%Y-%m-%d'),
                'end_date': s.end_date.strftime('%Y-%m-%d'),
                # Add quarter calculation data for the static timeline
                'start_year': start_year,
                'start_month': start_month,
                'start_quarter': start_quarter,
                'end_year': end_year,
                'end_month': end_month,
                'end_quarter': end_quarter,
                'quarter_start_pos': start_pos,
                'quarter_end_pos': end_pos,
                'quarter_width': width,
                # Add number and visibility flag for template
                'number': stage_number,
                'should_show_number': should_show_number
            })
        
        stage_bars.sort(key=lambda x: x['start_date'])
        
        demand_position = {
            'start_percent': demand_start_percent,
            'width_percent': demand_width_percent,
            'start_date': demand_start.strftime('%Y-%m-%d'),
            'end_date': demand_end.strftime('%Y-%m-%d'),
            'duration_days': demand_duration_days
        }
        
        demand_data.append({
            'demand': demand, 
            'stages': stage_bars,
            'position': demand_position
        })

    # === Stage Legend ===
    stage_legend = []
    # Make sure we create entries for ALL possible stages, in order
    for stage_key, number in sorted(STAGE_ORDER.items(), key=lambda x: x[1]):
        label = Stage(stage_key).label
        color = STAGE_COLORS.get(stage_key, '#888')
        stage_legend.append({'number': number, 'label': label, 'color': color})
        # print(f"Added stage: {number}. {label} with color {color}")
    
    # Ensure we have all stages (debug check)
    print(f"Generated {len(stage_legend)} stage legend entries")

    return render(request, 'trackerapp/demand_list.html', {
        'demand_data': demand_data,
        'stage_legend': stage_legend,
        'timeline_markers': quarter_markers,
        'month_markers': month_markers,
        'timeline_years': timeline_years,
        'global_timeline_start': global_timeline_start.strftime('%Y-%m-%d'),
        'global_timeline_end': global_timeline_end.strftime('%Y-%m-%d'),
    })

def add_demand(request):
    if request.method == "POST":
        form = DemandForm(request.POST)
        if form.is_valid():
            # Save the demand with the form data
            demand = form.save()
            
            # Get the start date and duration from the form
            start_date = form.cleaned_data['start_date']
            duration_months = form.cleaned_data['duration_months']
            
            # Calculate the end date based on start date and duration in months
            # Adding months is tricky due to varying month lengths
            # This approach adds the specified number of months
            end_date = start_date.replace(year=start_date.year + ((start_date.month - 1 + duration_months) // 12),
                                         month=((start_date.month - 1 + duration_months) % 12) + 1)
            
            # Create an initial dark grey mini progress bar for the new demand
            # This will be a mini progress bar that spans exactly the demand's duration
            DemandStagePeriod.objects.create(
                demand=demand,
                stage='mini_progress',  # Using a custom stage identifier for mini progress bar
                start_date=start_date,
                end_date=end_date
            )
            
            return redirect('demand_list')
    else:
        form = DemandForm()
    return render(request, 'trackerapp/add_demand.html', {'form': form})

def edit_demand(request, demand_id):
    demand = get_object_or_404(Demand, id=demand_id)
    if request.method == 'POST':
        form = DemandForm(request.POST, instance=demand)
        if form.is_valid():
            demand = form.save()
            
            # Get the updated start date and duration from the form
            start_date = form.cleaned_data['start_date']
            duration_months = form.cleaned_data['duration_months']
            
            if start_date and duration_months:
                # Calculate the end date based on start date and duration in months
                end_date = start_date.replace(year=start_date.year + ((start_date.month - 1 + duration_months) // 12),
                                          month=((start_date.month - 1 + duration_months) % 12) + 1)
                
                # Check if this demand has a mini progress bar
                mini_bar = demand.stages.filter(stage='mini_progress').first()
                
                if mini_bar:
                    # Update the existing mini progress bar
                    mini_bar.start_date = start_date
                    mini_bar.end_date = end_date
                    mini_bar.save()
                else:
                    # Create a new mini progress bar if none exists
                    DemandStagePeriod.objects.create(
                        demand=demand,
                        stage='mini_progress',  # Using custom mini_progress stage
                        start_date=start_date,
                        end_date=end_date
                    )
            
            messages.success(request, 'Demand updated successfully.')
            return redirect('demand_list')
    else:
        form = DemandForm(instance=demand)
    
    return render(request, 'trackerapp/edit_demand.html', {
        'form': form,
        'demand': demand
    })

def delete_demand(request, demand_id):
    demand = get_object_or_404(Demand, id=demand_id)
    demand.delete()
    messages.success(request, 'Demand deleted successfully.')
    return redirect('demand_list')

def update_stage(request):
    error_message = None
    
    if request.method == "POST":
        form = DemandStagePeriodForm(request.POST)
        if form.is_valid():
            # Get the demand and stage from the form
            demand = form.cleaned_data['demand']
            new_stage = form.cleaned_data['stage']
            
            # Get the stage number for the new stage
            new_stage_number = STAGE_ORDER.get(new_stage, -1)
            
            # Get existing stages for this demand
            existing_stages = DemandStagePeriod.objects.filter(demand=demand)
            existing_stage_numbers = [STAGE_ORDER.get(s.stage, -1) for s in existing_stages]
            
            # Check if this is the first stage (should be 0) or follows the sequence
            valid_sequence = True
            if existing_stages.exists():
                # If there are existing stages, the new one should be the next in sequence
                max_existing_number = max(existing_stage_numbers)
                if new_stage_number != max_existing_number + 1:
                    valid_sequence = False
                    error_message = f"Invalid stage sequence. Expected stage {max_existing_number + 1}, but got {new_stage_number}."
            else:
                # If this is the first stage, it should be 0
                if new_stage_number != 0:
                    valid_sequence = False
                    error_message = f"First stage must be 0 (Demand to be Initiated), but got {new_stage_number}."
            
            if valid_sequence:
                # Save the new stage
                new_stage_period = form.save()
                
                # Update the mini progress bar to match the current stage
                demand = new_stage_period.demand
                mini_bar = demand.stages.filter(stage='mini_progress').first()
                
                if mini_bar:
                    # Get start date and duration from the demand
                    start_date = demand.start_date
                    duration_months = demand.duration_months
                    
                    # Calculate the end date based on duration
                    if start_date and duration_months:
                        end_date = start_date.replace(
                            year=start_date.year + ((start_date.month - 1 + duration_months) // 12),
                            month=((start_date.month - 1 + duration_months) % 12) + 1
                        )
                        
                        # Update the mini bar's start and end dates but keep the 'mini_progress' identifier
                        mini_bar.start_date = start_date
                        mini_bar.end_date = end_date
                        mini_bar.save()
                        
                        # Store the current stage information in the session to use in the template
                        if 'demand_current_stages' not in request.session:
                            request.session['demand_current_stages'] = {}
                        
                        # Map the demand ID to its current stage
                        demand_current_stages = request.session.get('demand_current_stages', {})
                        demand_current_stages[str(demand.id)] = new_stage_period.stage
                        request.session['demand_current_stages'] = demand_current_stages
                        # Make sure the session is saved
                        request.session.modified = True
                
                return redirect('demand_list')
        
    else:
        form = DemandStagePeriodForm()
    
    # Prepare stage reference with numbering
    stage_order = {}
    for stage_key, number in sorted(STAGE_ORDER.items(), key=lambda x: x[1]):
        stage_order[Stage(stage_key)] = number
        
    return render(request, 'trackerapp/update_stage.html', {
        'form': form,
        'stage_order': stage_order,
        'error_message': error_message,
        'stage_colors': STAGE_COLORS,
    })

def edit_stage_dates(request):
    if request.method == 'POST':
        stage_id = request.POST.get('stage_id')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')

        stage_period = get_object_or_404(DemandStagePeriod, id=stage_id)
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            # Invalid date format, just ignore or handle error
            return redirect('demand_list')

        if start_date <= end_date:
            stage_period.start_date = start_date
            stage_period.end_date = end_date
            stage_period.save()

        return redirect('demand_list')